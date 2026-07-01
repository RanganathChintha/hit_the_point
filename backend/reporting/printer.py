from config import SEP, OK, ERR, WARN, INFO

def _has_issues(report: dict) -> bool:
    """Return True if the report contains any mismatch or missing data."""
    if not report["found_in_magento"]:
        return True
    tc = report.get("type_comparison")
    if tc and not tc["types_match"]:
        return True
    bc = report.get("bundle_comparison")
    if bc and (
        not bc["slot_count_match"]
        or bc["slots_only_in_pim"]
        or bc["slots_only_in_magento"]
        or any(
            not sd["count_match"] or sd["skus_only_in_pim"] or sd["skus_only_in_magento"]
            for sd in bc["per_slot"].values()
        )
    ):
        return True
    cc = report.get("configurable_comparison")
    if cc and (
        not cc["count_match"]
        or cc["skus_only_in_pim"]
        or cc["skus_only_in_magento"]
    ):
        return True
    catc = report.get("category_comparison")
    if catc and not catc["matches"]:
        return True
    return False

def print_report(report: dict) -> None:
    """Print a detailed report for one SKU — only if issues exist."""
    if not _has_issues(report):
        return

    print(f"\n{SEP}")
    print(f"  SKU : {report['sku']}")
    print(SEP)
    print(f"  PIM    : {'Found' if report['found_in_pim']    else 'NOT FOUND'}")
    print(f"  Magento : {'Found' if report['found_in_magento'] else 'NOT FOUND'}")

    if not report["found_in_magento"]:
        print(f"\n  {ERR} SKU exists in PIM but is MISSING in Magento.")
        print(SEP)
        return

    tc = report.get("type_comparison")
    if tc:
        print(f"\n{'TYPE COMPARISON':─<70}")
        print(f"  PIM type    : {tc['pim_type']}")
        print(f"  Magento type : {tc['magento_type']}")
        if tc["types_match"]:
            print(f"  {OK}  Types compatible.")
        else:
            print(f"  {ERR} TYPE MISMATCH: {tc['mismatch_note']}")

    bc = report.get("bundle_comparison")
    if bc:
        print(f"\n{'BUNDLE SLOT COMPARISON':─<70}")
        print(f"  PIM    slots : {bc['pim_slot_count']}")
        print(f"  Magento slots : {bc['magento_slot_count']}")
        print(f"  {OK if bc['slot_count_match'] else ERR}  Slot count {'matches' if bc['slot_count_match'] else 'MISMATCH'}.")
        if bc["slots_only_in_pim"]:
            print(f"\n  {ERR} Slots in PIM but MISSING in Magento : {bc['slots_only_in_pim']}")
        if bc["slots_only_in_magento"]:
            print(f"  {INFO} Slots in Magento but NOT in PIM     : {bc['slots_only_in_magento']}")
        for slot_name, sd in bc["per_slot"].items():
            if sd["count_match"] and not sd["skus_only_in_pim"] and not sd["skus_only_in_magento"]:
                continue
            print(f"\n  [{slot_name.upper()}]")
            print(f"    PIM    SKU count : {sd['pim_sku_count']}")
            print(f"    Magento SKU count : {sd['magento_sku_count']}")
            if not sd["count_match"]:
                print(f"    {ERR} Child count MISMATCH.")
            if sd["skus_only_in_pim"]:
                print(f"    {ERR} In PIM but MISSING in Magento : {sd['skus_only_in_pim']}")
            if sd["skus_only_in_magento"]:
                print(f"    {INFO} In Magento but NOT in PIM    : {sd['skus_only_in_magento']}")

    cc = report.get("configurable_comparison")
    if cc:
        print(f"\n{'CONFIGURABLE CHILD COMPARISON':─<70}")
        print(f"  PIM    child count : {cc['pim_child_count']}")
        print(f"  Magento child count : {cc['magento_child_count']}")
        print(f"  {OK if cc['count_match'] else ERR}  Child count {'matches' if cc['count_match'] else 'MISMATCH'}.")
        if cc["unresolved_magento_ids"]:
            print(f"  {WARN} Unresolved Magento IDs        : {cc['unresolved_magento_ids']}")
        if cc["skus_only_in_pim"]:
            print(f"  {ERR} In PIM but MISSING in Magento : {cc['skus_only_in_pim']}")
        if cc["skus_only_in_magento"]:
            print(f"  {INFO} In Magento but NOT in PIM    : {cc['skus_only_in_magento']}")

    catc = report.get("category_comparison")
    if catc:
        print(f"\n{'CATEGORY LINK COMPARISON':─<70}")
        print(f"  PIM categories : {catc['pim_category_ids']}")
        print(f"  Magento links  : {catc['magento_category_ids']}")
        print(f"  {OK if catc['matches'] else ERR}  Category links {'match' if catc['matches'] else 'MISMATCH'}.")
        if catc["missing_in_magento"]:
            print(f"  {ERR} PIM categories missing in Magento : {catc['missing_in_magento']}")
        if catc["extra_in_magento"]:
            print(f"  {INFO} Magento-only categories           : {catc['extra_in_magento']}")
        if catc["position_mismatches"]:
            print(f"  {WARN} Position mismatches               : {catc['position_mismatches']}")
        if catc["unknown_categories"]:
            print(f"  {WARN} Unknown category IDs              : {catc['unknown_categories']}")

    print(SEP)

def summarize_batch(reports: list) -> None:
    """Print a summary table and all detailed issues from a batch run."""
    total      = len(reports)
    missing    = [r for r in reports if not r["found_in_magento"]]
    type_mm    = [r for r in reports if r.get("type_comparison") and not r["type_comparison"]["types_match"]]
    bundle_iss = [r for r in reports if _has_issues(r) and r.get("bundle_comparison")]
    config_iss = [r for r in reports if _has_issues(r) and r.get("configurable_comparison")]
    category_iss = [r for r in reports if _has_issues(r) and r.get("category_comparison") and not r["category_comparison"]["matches"]]
    perfect    = [r for r in reports if not _has_issues(r)]

    print(f"\n{'BATCH SUMMARY  (PIM → Magento)':═<70}")
    print(f"  Total PIM SKUs compared     : {total}")
    print(f"  {OK}  Perfect matches           : {len(perfect)}")
    print(f"  {ERR} Missing in Magento         : {len(missing)}")
    print(f"  {ERR} Type mismatches           : {len(type_mm)}")
    print(f"  {ERR} Bundle slot issues        : {len(bundle_iss)}")
    print(f"  {ERR} Configurable child issues : {len(config_iss)}")
    print(f"  {ERR} Category link issues      : {len(category_iss)}")
    print("═" * 70)

    if missing:
        print(f"\n  {ERR} PIM SKUs MISSING in Magento ({len(missing)}):")
        for r in missing:
            pt = r["type_comparison"]["pim_type"] if r["type_comparison"] else "?"
            print(f"    • {r['sku']:<40}  [{pt}]")

    if type_mm:
        print(f"\n  {ERR} TYPE MISMATCHES ({len(type_mm)}):")
        for r in type_mm:
            tc = r["type_comparison"]
            print(f"    • {r['sku']:<40}  PIM={tc['pim_type']}  Magento={tc['magento_type']}")

    if bundle_iss:
        print(f"\n  {ERR} BUNDLE ISSUES ({len(bundle_iss)}):")
        for r in bundle_iss:
            print(f"    • {r['sku']}")

    if config_iss:
        print(f"\n  {ERR} CONFIGURABLE ISSUES ({len(config_iss)}):")
        for r in config_iss:
            print(f"    • {r['sku']}")

    if category_iss:
        print(f"\n  {ERR} CATEGORY LINK ISSUES ({len(category_iss)}):")
        for r in category_iss:
            print(f"    • {r['sku']}")

    issues = [r for r in reports if _has_issues(r)]
    if issues:
        print(f"\n{'DETAILED ISSUES':═<70}")
        for r in issues:
            print_report(r)
    else:
        print(f"\n  {OK}  No issues found — PIM and Magento are fully in sync!")

# ─────────────────────────────────────────────
#  MARKET REPORT PRINTERS
# ─────────────────────────────────────────────

def print_all_markets(markets: list) -> None:
    """Print a table of all markets and their product counts."""
    print(f"\n{'MARKET OVERVIEW  (PIM — customerLabels)':═<70}")
    print(f"  {'CODE':<8}  {'COUNT':>6}   DESCRIPTION")
    print(f"  {'─'*6}  {'─'*6}   {'─'*40}")
    for m in markets:
        print(f"  {m['code']:<8}  {m['count']:>6}   {m['description']}")
    print("═" * 70)
    print(f"  Total markets : {len(markets)}")
    print("═" * 70)

def print_market_detail(detail: dict) -> None:
    """Print full detail for one market — count + breakdown by product type."""
    print(f"\n{'═' * 70}")
    print(f"  MARKET : {detail['code']}  —  {detail['description']}")
    print(f"  Total products : {detail['count']}")
    print("═" * 70)

    print(f"\n{'BREAKDOWN BY PRODUCT TYPE':─<70}")
    for ptype, skus in sorted(detail["by_type"].items()):
        print(f"  {ptype:<20} : {len(skus):>5} products")

    print(f"\n{'PRODUCT LIST':─<70}")
    print(f"  {'SKU':<20}  {'TYPE':<20}  NAME")
    print(f"  {'─'*18}  {'─'*18}  {'─'*28}")
    for p in detail["skus"]:
        name_preview = p["name"][:40] if p["name"] else "—"
        print(f"  {p['sku']:<20}  {p['product_type']:<20}  {name_preview}")
    print("═" * 70)
