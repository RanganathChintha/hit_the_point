def normalize_slot(name: str) -> str:
    if not name:
        return ""
    return name.strip().lower().replace(" ", "_").replace("-", "_")

def _get_custom_attr(custom_attributes: list, code: str):
    """Return the value of a custom attribute by attribute_code."""
    for attr in custom_attributes:
        if attr.get("attribute_code") == code:
            return attr.get("value")
    return None

def parse_magento_products(data) -> dict:
    """
    Parse raw Magento (Magento) JSON into a flat SKU-keyed dict.
    Handles simple, configurable, and bundle types.
    """
    result = {}
    items = data if isinstance(data, list) else data.get("items", [data])

    for prod in items:
        if not isinstance(prod, dict):
            continue
        sku     = prod.get("sku")
        type_id = prod.get("type_id", "simple")
        if not sku:
            continue

        entry = {
            "sku":                    sku,
            "name":                   prod.get("name", ""),
            "type_id":                type_id,
            "configurable_options":   [],
            "configurable_child_ids": [],
            "bundle_slots":           {},
            "category_links":         [],
            "custom_attributes":      prod.get("custom_attributes", []),
        }

        ext = prod.get("extension_attributes", {})
        entry["category_links"] = ext.get("category_links", [])

        if type_id == "configurable":
            entry["configurable_child_ids"] = list(
                ext.get("configurable_product_links", [])
            )
            for opt in ext.get("configurable_product_options", []):
                entry["configurable_options"].append({
                    "label":         opt.get("label", ""),
                    "attribute_id":  opt.get("attribute_id"),
                    "value_indexes": [
                        v["value_index"]
                        for v in opt.get("values", [])
                        if "value_index" in v
                    ],
                })

        elif type_id == "bundle":
            for slot in ext.get("bundle_product_options", []):
                raw_title  = slot.get("title", "")
                norm_title = normalize_slot(raw_title)
                child_skus = [
                    pl["sku"]
                    for pl in slot.get("product_links", [])
                    if pl.get("sku")
                ]
                if norm_title in entry["bundle_slots"]:
                    entry["bundle_slots"][norm_title]["skus"].extend(child_skus)
                else:
                    entry["bundle_slots"][norm_title] = {
                        "title":    norm_title,
                        "required": slot.get("required", False),
                        "type":     slot.get("type", "select"),
                        "skus":     child_skus,
                    }

        result[sku] = entry

    return result

def build_magento_id_to_sku(data) -> dict:
    """Build a { internal_id (int) -> sku (str) } map from Magento products."""
    id_to_sku = {}
    items = data if isinstance(data, list) else data.get("items", [data])
    for prod in items:
        if isinstance(prod, dict) and prod.get("id") and prod.get("sku"):
            id_to_sku[int(prod["id"])] = prod["sku"]
    return id_to_sku

def build_magento_category_map(magento_cat_tree: list) -> dict:
    """
    Recursively flatten the nested Magento category tree into:
        { id -> { name, parent_id, level } }
    """
    cat_map = {}

    def recurse(nodes):
        for node in nodes:
            cat_map[node["id"]] = {
                "name":      node.get("name", "Unknown"),
                "parent_id": node.get("parent_id"),
                "level":     node.get("level", 0),
            }
            recurse(node.get("children_data", []))

    recurse(magento_cat_tree)
    return cat_map

def extract_magento_categories(data) -> list:
    """Extract the root list from magento_categories.json."""
    if isinstance(data, list):
        return data
    for key in ("children_data", "categories", "data", "items"):
        if isinstance(data, dict) and key in data:
            val = data[key]
            if isinstance(val, list):
                return val
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list):
                return v
    return []
