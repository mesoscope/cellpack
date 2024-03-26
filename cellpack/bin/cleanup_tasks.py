from cellpack.autopack.DBRecipeHandler import DBMaintenance
from cellpack.autopack.interface_objects.database_ids import DATABASE_IDS


def run_cleanup(db_id=DATABASE_IDS.FIREBASE):
    """
    Performs cleanup operations on expired database entries.
    This function is executed as part of a scheduled task defined in .github/workflows/cleanup-firebase.yml

    Args:
        db_id(str): The database id to use
    """
    handler = DATABASE_IDS.handlers().get(db_id)
    initialized_db = handler(default_db="staging")
    db_maintainer = DBMaintenance(initialized_db)
    db_maintainer.cleanup_results()


if __name__ == "__main__":
    run_cleanup()
