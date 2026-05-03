from typing import List

from pydantic import BaseModel


class AddAssociazioneRequest(BaseModel):
    username: str
    parole: List[str]