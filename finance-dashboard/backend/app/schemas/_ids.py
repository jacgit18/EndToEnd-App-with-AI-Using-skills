"""Bounds for client-supplied row ids.

Primary keys are 32-bit INTEGER columns. Without an upper bound a request like
`account_id=99999999999999999999` reaches Postgres as an out-of-range parameter and
comes back as an uncaught DataError (a 500); with it, it's a 422 at the edge, like
any other malformed input. Ids start at 1.
"""

from typing import Annotated

from pydantic import Field

MAX_ID = 2**31 - 1  # largest value an INTEGER primary key can hold

# Request-body fields use `Id`; Path/Query/Form parameters spell the same bounds as
# `Path(ge=1, le=MAX_ID)` because FastAPI's parameter classes take them directly.
Id = Annotated[int, Field(ge=1, le=MAX_ID)]
