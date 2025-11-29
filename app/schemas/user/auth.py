from pydantic import BaseModel, Field

class Login(BaseModel):
    email: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class ChangePasswordRequest(BaseModel):
    old_password: str = Field(..., min_length=6, max_length=32)
    new_password: str = Field(..., min_length=6, max_length=32)
