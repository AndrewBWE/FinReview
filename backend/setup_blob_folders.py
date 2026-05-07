"""
One-time script to pre-populate the blob container with lender folders.
Each folder gets a small _init placeholder so it exists as a virtual directory.

Run from the backend directory:
    python setup_blob_folders.py [--dry-run]
"""
import sys
from dotenv import load_dotenv

load_dotenv()

from storage import _container_client

DRY_RUN = "--dry-run" in sys.argv

LENDER_FOLDERS = [
    "001 - Thrivent",
    "003 - American Fidelity",
    "004 - Nationwide",
    "006 - Genworth",
    "007 - State Farm",
    "008 - Sun Life",
    "009 - Lincoln",
    "012 - Empower",
    "013 - Corebridge Financial (fka AIG)",
    "013 - Situs",
    "014 - Voya",
    "016 - PPM",
    "018 - American Equity",
    "019 - Farm Bureau",
    "020 - Farm Bureau MI",
    "021 - Protective",
    "027 - One America",
    "057 - Guardian",
    "058 - Columbian Mutual",
    "062 - KCL",
    "063 - UNUM",
    "068 - PIMCO",
    "070 - CorAmerica",
    "071 - CNA",
    "072 - JPM",
    "074 - Everlake",
    "075 - ANICO",
    "076 - Arrowmark",
    "077 - Woodmen",
    "078 - Assurity",
    "300 - TurnCap",
]


def main():
    cc = _container_client()
    print(f"{'[DRY RUN] ' if DRY_RUN else ''}Target container: {cc.container_name}\n")
    print(f"Creating {len(LENDER_FOLDERS)} lender folders...")

    for folder in LENDER_FOLDERS:
        blob_path = f"{folder}/_init"
        print(f"  {blob_path}")
        if not DRY_RUN:
            cc.get_blob_client(blob_path).upload_blob(b"", overwrite=True)

    print(f"\n{'[DRY RUN] ' if DRY_RUN else ''}Done. {len(LENDER_FOLDERS)} lender folders created.")


if __name__ == "__main__":
    main()
