def group_by(
    group_by: str,
    fields: list[str],
) -> dict:
    """Group by `group_by` field and aggregate all other fields with `last` function

    `groupBy` transformation with `groupby` operation and `aggregations` set to `last` for all fields

    Args:
        group_by: field to group by
        fields: list of fields to aggregate

    Returns:
        transformation dict
    """

    if group_by in fields:
        fields.remove(group_by)

    transformaton = {
        "id": "groupBy",
        "options": {
            "fields": {
                "id": {
                    "aggregations": [],
                    "operation": "groupby",
                }
            }
        },
    }

    for field_name in fields:
        transformaton["options"]["fields"][field_name] = {
            "aggregations": ["last"],
            "operation": "aggregate",
        }

    return transformaton


def concat_fields(alias: str, fields: list[str]) -> dict:
    """Concatenate all unique values from `fields` into a single field and rename it to `alias`

    Alias to `calculateField` transformation with mode `reduceRow` and reducer `uniqueValues`

    Args:
        alias: how to name the new field
        fields: list of fields to concatenate

    Returns:
        transformation dict
    """
    return {
        "id": "calculateField",
        "options": {
            "mode": "reduceRow",
            "reduce": {
                "reducer": "uniqueValues",
                "include": fields,
            },
            "alias": alias,
            "replaceFields": False,
        },
    }


def organize(
    exclude_by_name: list[str] = [],
    index_by_name: list[str] = [],
    rename_by_name: dict[str, str] = {},
) -> dict:
    """Organize fields either by excluding, indexing or renaming them

    `organize` transformation with `excludeByName`, `indexByName` and `renameByName` options

    Args:
        exclude_by_name: list of fields to exclude
        index_by_name: list of ordered fields. `enumerate` will be used to create the index
        rename_by_name: dict of fields to rename (`{from: to}`)

    Returns:
        transformation dict
    """
    if not any([exclude_by_name, index_by_name, rename_by_name]):
        raise ValueError("At least one of the parameters must be set")

    return {
        "id": "organize",
        "options": {
            "excludeByName": {name: True for name in exclude_by_name},
            "indexByName": {name: i for i, name in enumerate(index_by_name)}
            if len(index_by_name) > 0
            else {},
            "renameByName": rename_by_name,
        },
    }
