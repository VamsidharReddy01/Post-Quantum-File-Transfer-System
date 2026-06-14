from django.db import migrations


def sync_live_schema(apps, schema_editor):
    if schema_editor.connection.vendor != "mysql":
        return

    with schema_editor.connection.cursor() as cursor:
        database_name = schema_editor.connection.settings_dict["NAME"]

        def column_exists(table_name, column_name):
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.columns
                WHERE table_schema = %s
                  AND table_name = %s
                  AND column_name = %s
                """,
                [database_name, table_name, column_name],
            )
            return cursor.fetchone()[0] > 0

        def index_exists(table_name, index_name):
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.statistics
                WHERE table_schema = %s
                  AND table_name = %s
                  AND index_name = %s
                """,
                [database_name, table_name, index_name],
            )
            return cursor.fetchone()[0] > 0

        transfer_table = "filetransfer_filetransfer"
        audit_table = "filetransfer_auditlog"

        if column_exists(transfer_table, "file_hash"):
            schema_editor.execute(
                "ALTER TABLE `filetransfer_filetransfer` MODIFY `file_hash` varchar(64) NOT NULL"
            )

        missing_columns = {
            "aes_nonce": "`aes_nonce` longblob NOT NULL",
            "aes_tag": "`aes_tag` longblob NOT NULL",
            "expires_at": "`expires_at` datetime(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)",
            "download_limit": "`download_limit` integer UNSIGNED NOT NULL DEFAULT 1",
            "download_count": "`download_count` integer UNSIGNED NOT NULL DEFAULT 0",
            "encryption_time_ms": "`encryption_time_ms` integer UNSIGNED NOT NULL DEFAULT 0",
            "decryption_time_ms": "`decryption_time_ms` integer UNSIGNED NOT NULL DEFAULT 0",
            "kyber_time_ms": "`kyber_time_ms` integer UNSIGNED NOT NULL DEFAULT 0",
            "dilithium_time_ms": "`dilithium_time_ms` integer UNSIGNED NOT NULL DEFAULT 0",
        }

        for column_name, column_sql in missing_columns.items():
            if not column_exists(transfer_table, column_name):
                schema_editor.execute(
                    f"ALTER TABLE `filetransfer_filetransfer` ADD COLUMN {column_sql}"
                )

        indexes = [
            (
                transfer_table,
                "filetransfe_sender__8340d0_idx",
                "CREATE INDEX `filetransfe_sender__8340d0_idx` "
                "ON `filetransfer_filetransfer` (`sender_id`, `created_at`)",
            ),
            (
                transfer_table,
                "filetransfe_receive_7fac32_idx",
                "CREATE INDEX `filetransfe_receive_7fac32_idx` "
                "ON `filetransfer_filetransfer` (`receiver_id`, `status`)",
            ),
            (
                transfer_table,
                "filetransfe_status_40b91b_idx",
                "CREATE INDEX `filetransfe_status_40b91b_idx` "
                "ON `filetransfer_filetransfer` (`status`, `expires_at`)",
            ),
            (
                audit_table,
                "filetransfe_user_id_80198c_idx",
                "CREATE INDEX `filetransfe_user_id_80198c_idx` "
                "ON `filetransfer_auditlog` (`user_id`, `timestamp`)",
            ),
            (
                audit_table,
                "filetransfe_action_644fa3_idx",
                "CREATE INDEX `filetransfe_action_644fa3_idx` "
                "ON `filetransfer_auditlog` (`action`)",
            ),
        ]

        for table_name, index_name, index_sql in indexes:
            if not index_exists(table_name, index_name):
                schema_editor.execute(index_sql)


class Migration(migrations.Migration):
    atomic = False

    dependencies = [
        ("filetransfer", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(sync_live_schema, reverse_code=migrations.RunPython.noop),
    ]
