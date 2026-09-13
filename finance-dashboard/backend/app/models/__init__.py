"""Import every model so that `Base.metadata` knows all the tables.

Alembic's autogenerate (and any `Base.metadata.create_all`) only sees a table
if its model class has been imported first. Importing this package — `import
app.models` — pulls all of them in.
"""

from app.models.account import Account
from app.models.budget import Budget
from app.models.category import Category
from app.models.import_batch import ImportBatch
from app.models.session import AuthSession
from app.models.transaction import Transaction

__all__ = [
    "Account",
    "Budget",
    "Category",
    "ImportBatch",
    "AuthSession",
    "Transaction",
]
