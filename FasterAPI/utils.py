import asyncio
import pickle
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509 import Certificate, CertificateSigningRequest
from cryptography.x509.oid import NameOID
from fastapi import HTTPException, status
from jose import jwt
from sqlalchemy.orm import Session

from . import ALGORITHM, SECRET_KEY, TOKEN_EXPIRATION_TIME, get_db, logger, pwd_context
from .models import ActiveSession, BlacklistedToken, User
from .schemas import UserCreate


def verify_password(plain_password, hashed_password):
    """Verifies the password."""
    return pwd_context.verify(plain_password, hashed_password)


async def authenticate_user(db: Session, username: str, password: str):
    """Authenticates the user."""
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict):
    """Creates a JWT token for authenticated user."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=TOKEN_EXPIRATION_TIME)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def create_session(token: str, db: Session, client: str):
    """Activates the token upon user login."""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username = payload["sub"]
    exp = datetime.fromtimestamp(payload["exp"])
    existing_active_session = (
        db.query(ActiveSession).filter(
            ActiveSession.username == username).first()
    )
    if existing_active_session:
        existing_active_session.client = client  # type: ignore
        existing_active_session.exp = exp  # type: ignore
        db.commit()
    else:
        token_to_activate = ActiveSession(
            username=username, client=client, exp=exp)
        db.add(token_to_activate)
        db.commit()


def blacklist_token(token: str, db: Session):
    """Blacklists the token upon user logout."""
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    exp = datetime.fromtimestamp(payload["exp"])
    token_to_blacklist = BlacklistedToken(token=token, exp=exp)
    db.add(token_to_blacklist)
    db.commit()


def register_user(user: UserCreate):
    """Registers a new user."""
    db = next(get_db())
    extsing_user = db.query(User).filter(
        User.username == user.username).first()
    if extsing_user:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="User already exists.",
        )
    new_user = User(
        username=user.username,
        hashed_password=pwd_context.hash(user.password),
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        is_superuser=user.is_superuser,
    )
    db.add(new_user)
    db.commit()
    logger.debug(f"User {user.username} registered.")
    return user


def create_superuser(
    username: str,
    password: str,
    first_name: str,
    last_name: str,
    email: str,
):
    """Creates a superuser."""
    superuser = UserCreate(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=password,
        is_superuser=True,
    )

    def _load_superusers() -> List[UserCreate]:
        try:
            with open(".superuser", "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            return []

    def _save_superusers(superusers: List[UserCreate]):
        with open(".superuser", "wb") as f:
            pickle.dump(superusers, f)

    superusers = _load_superusers()
    superusers.append(superuser)
    _save_superusers(superusers)


def create_user(
    username: str,
    password: str,
    first_name: str,
    last_name: str,
    email: str,
):
    """Creates a user."""
    user = UserCreate(
        username=username,
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=password,
        is_superuser=False,
    )

    def _load_users() -> List[UserCreate]:
        try:
            with open(".users", "rb") as f:
                return pickle.load(f)
        except FileNotFoundError:
            return []

    def _save_users(users: List[UserCreate]):
        with open(".users", "wb") as f:
            pickle.dump(users, f)

    users = _load_users()
    users.append(user)
    _save_users(users)


# define neccessary functions
async def _clean_up_expired_tokens():
    """A async task to cleanup expired tokens from the database. Maintains a optimal performance."""
    while True:
        db = next(get_db())
        db.query(BlacklistedToken).filter(
            BlacklistedToken.exp < datetime.now()
        ).delete()
        db.commit()
        db.close()
        logger.debug("Expired tokens cleaned up.")
        await asyncio.sleep(TOKEN_EXPIRATION_TIME * 60)


def generate_root_ca(
    expiration_days: int = 3650,
    common_name: str = "Root CA",
    subject_alternative_names: Optional[List[str]] = None,
    directory: Optional[str] = None,
) -> Tuple[rsa.RSAPrivateKey, Certificate]:
    """Create a root CA certificate and private key.

    Args:
        expiration_days (int, optional): the nuber of days before expiration. Defaults to 3650.
        common_name (str, optional): the common name. Defaults to "Root CA".
        subject_alternative_names (Optional[List[str]], optional): the subject alternative names. Defaults to None.
        directory (Optional[str], optional): the directory to save the files. Defaults to None.

    Returns:
        Tuple[rsa.RSAPrivateKey, Certificate]: returns the CA key and certifcate
    """

    key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
    )

    builder = x509.CertificateBuilder()
    builder = builder.subject_name(subject)
    builder = builder.issuer_name(issuer)
    builder = builder.public_key(key.public_key())
    builder = builder.serial_number(x509.random_serial_number())
    builder = builder.not_valid_before(datetime.now(timezone.utc))
    builder = builder.not_valid_after(
        datetime.now(timezone.utc) + timedelta(days=expiration_days)
    )
    builder = builder.add_extension(
        x509.BasicConstraints(ca=True, path_length=None),
        critical=True,
    )
    if subject_alternative_names:
        san_dns_names = x509.SubjectAlternativeName(
            [x509.DNSName(name) for name in subject_alternative_names]
        )
        builder = builder.add_extension(san_dns_names, critical=False)
    cert = builder.sign(key, hashes.SHA256(), default_backend())

    if directory:
        with open(f"{directory}/root-key.pem", "wb") as f:
            f.write(
                key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
        with open(f"{directory}/root-cert.pem", "wb") as f:
            f.write(cert.public_bytes(encoding=serialization.Encoding.PEM))

    return key, cert


def generate_key_and_csr(
    common_name: str, san_dns_names: List[str], directory: Optional[str] = None
) -> Tuple[rsa.RSAPrivateKey, CertificateSigningRequest]:
    """Generate a private key and certificate signing request (CSR).

    Args:
        common_name (str): the common name of the server.
        san_dns_names (List[str]): the subject alternative names of the server.
        directory (Optional[str], optional): the directory to save the files. Defaults to None.

    Returns:
        Certificate: returns the sever private key and certifcate signing request.
    """
    key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    subject = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]
    )

    if san_dns_names:
        extensions = x509.SubjectAlternativeName(
            [x509.DNSName(name) for name in san_dns_names]
        )
    else:
        extensions = x509.SubjectAlternativeName(
            [x509.DNSName(common_name)]
        )

    csr = (
        x509.CertificateSigningRequestBuilder()
        .subject_name(subject)
        .add_extension(extensions, critical=False)
        .sign(key, hashes.SHA256(), default_backend())
    )

    if directory:
        with open(f"{directory}/server-key.pem", "wb") as f:
            f.write(
                key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
        with open(f"{directory}/server-csr.pem", "wb") as f:
            f.write(csr.public_bytes(encoding=serialization.Encoding.PEM))

    return key, csr


def sign_certificate(
    csr: CertificateSigningRequest,
    issuer_key: Optional[rsa.RSAPrivateKey] = None,
    issuer_key_path: Optional[str] = None,
    issuer_cert: Optional[Certificate] = None,
    issuer_cert_path: Optional[str] = None,
    validity_days=365,
    directory: Optional[str] = None,
) -> Certificate:
    """Sign the certifcate signing request

    Args:
        csr (CertificateSigningRequest): the certificate signing request.
        issuer_key (Optional[rsa.RSAPrivateKey]): the issuer private key.
        issuer_key_path (Optional[str]): the issuer private key path.
        issuer_cert (Optional[Certificate]): the issuer certificate.
        issuer_cert_path (Optional[str]): the issuer certificate path.
        validity_days (int, optional): the number of days before expiration. Defaults to 365.
        directory (Optional[str], optional): the directory to save the files. Defaults to None.

    Raises:
        IssuerKeyNotDefined: raise if both issuer_key and issuer_key_path are provided or both ot provided.
        IssuerCertNotDefined: raise if both issuer_cert and issuer_cert_path are provided or both ot provided.

    Returns:
        Certificate: returns the signed certificate.
    """

    class IssuerKeyNotDefined(Exception):
        pass

    class IssuerCertNotDefined(Exception):
        pass

    if issuer_key and issuer_key_path is None:
        _issuer_key = issuer_key
    elif issuer_key_path and issuer_key is None:
        with open(issuer_key_path, "rb") as key_file:
            _issuer_key = serialization.load_pem_private_key(
                key_file.read(), password=None, backend=default_backend()
            )
    else:
        raise IssuerKeyNotDefined(
            "Either issuer_key or issuer_key_path must be provided.")

    if issuer_cert and issuer_cert_path is None:
        _issuer_cert = issuer_cert
    elif issuer_cert_path and issuer_cert is None:
        with open(issuer_cert_path, "rb") as cert_file:
            _issuer_cert = x509.load_pem_x509_certificate(
                cert_file.read(), default_backend()
            )
    else:
        raise IssuerCertNotDefined(
            "Either issuer_cert or issuer_cert_path must be provided.")

    cert = (
        x509.CertificateBuilder()
        .subject_name(csr.subject)
        .issuer_name(_issuer_cert.subject)
        .public_key(csr.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.now(timezone.utc))
        .not_valid_after(datetime.now(timezone.utc) + timedelta(days=validity_days))
        .add_extension(
            x509.BasicConstraints(ca=False, path_length=None),
            critical=True,
        )
        .add_extension(
            csr.extensions.get_extension_for_class(
                x509.SubjectAlternativeName).value,
            critical=False,
        )
        .sign(_issuer_key, hashes.SHA256(), default_backend())  # type: ignore
    )

    if directory:
        with open(f"{directory}/server-cert.pem", "wb") as f:
            f.write(cert.public_bytes(encoding=serialization.Encoding.PEM))
    return cert
