import validators
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from starlette.datastructures import URL

from . import crud, models, schemas
from .config import get_settings
from .database import SessionLocal, engine

tags_metadata = [
    {
        "name": "create",
        "description": "Request body contains the URL to be shortened",
    },
    {
        "name": "admin",
        "description": "Manage your shortened URLs. Requires the associated **secret key**",
    },
]

app = FastAPI()

v1 = FastAPI(
    title="urlCloud.xyz",
    description="Short Lived Shortened URLs for Short Term Needs",
    version="0.1.2",
    contact={
        "name": "Bryce Jenkins",
        "url": "https://github.com/thechainercygnus/urlcloud",
        "email": "bryce@durish.xyz",
    },
    openapi_tags=tags_metadata,
    docs_url=None,
    redoc_url="/",
)

models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def raise_bad_request(message):
    raise HTTPException(status_code=400, detail=message)


def raise_not_found(request):
    message = f"URL '{request.url}' doesn't exist"
    raise HTTPException(status_code=404, detail=message)


def get_admin_info(db_url: models.URL) -> schemas.URL:
    base_url = URL(get_settings().base_url)
    admin_endpoint = app.url_path_for(
        "administration info", secret_key=db_url.secret_key
    )
    redirect_endpoint = app.url_path_for("forwarder", url_key=db_url.key)
    db_url.url = str(base_url.replace(path=redirect_endpoint))
    db_url.admin_url = str(base_url.replace(path=admin_endpoint))
    return db_url


@v1.post("/url", response_model=schemas.URLInfo, tags=["create"])
def create_url(url: schemas.URLBase, db: Session = Depends(get_db)):
    if not validators.url(url.target_url):
        raise_bad_request(message="Your provided URL is not valid")

    db_url = crud.create_db_url(db=db, url=url)
    return get_admin_info(db_url)


@v1.get("/{url_key}", name="forwarder")
def forward_to_target_url(
    url_key: str, request: Request, db: Session = Depends(get_db)
):
    if db_url := crud.get_db_url_by_key(db=db, url_key=url_key):
        crud.update_db_clicks(db=db, db_url=db_url)
        return RedirectResponse(db_url.target_url)
    else:
        raise_not_found(request)


@v1.get(
    "/admin/{secret_key}",
    name="administration info",
    response_model=schemas.URLInfo,
    tags=["admin"],
)
def get_url_info(secret_key: str, request: Request, db: Session = Depends(get_db)):
    if db_url := crud.get_db_url_by_secret_key(db, secret_key):
        return get_admin_info(db_url)
    else:
        raise_not_found(request)


@v1.delete("/admin/{secret_key}", tags=["admin"])
def delete_url(secret_key: str, request: Request, db: Session = Depends(get_db)):
    if db_url := crud.deactivate_db_url_by_secret_key(db, secret_key=secret_key):
        message = f"Successfully deleted shortened URL for '{db_url.target_url}'"
        return {"detail": message}
    else:
        raise_not_found(request)


app.mount("/v1", v1)
