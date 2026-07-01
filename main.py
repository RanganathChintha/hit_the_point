import os
from config                      import get_magento_products_file, get_magento_cat_file, PIM_PRODUCTS_FILE, PIM_CAT_FILE, DATA_DIR
from pathlib import Path
from loaders.json_loader         import load_json
from loaders.pim_loader          import parse_pim_products
from loaders.magento_loader       import parse_magento_products, build_magento_id_to_sku, extract_magento_categories
from hierarchy.pim_hierarchy     import get_pim_hierarchy
from hierarchy.magento_hierarchy  import get_magento_hierarchy
from comparison.orchestrator     import compare_product, batch_compare
from reporting.printer           import print_report, summarize_batch, print_all_markets, print_market_detail
from reporting.html_reporter     import generate_html_report
from analysis.market_counter     import build_market_index, list_all_markets, get_market_products, search_market_by_description

def _load_all() -> dict:
    print("Loading files ...")
    magento_raw     = load_json(get_magento_products_file())
    magento_cat_raw = load_json(get_magento_cat_file())
    pim_raw        = load_json(PIM_PRODUCTS_FILE)
    pim_cat_raw    = load_json(PIM_CAT_FILE)

    print("Parsing ...")
    magento_map      = parse_magento_products(magento_raw)
    id_to_sku       = build_magento_id_to_sku(magento_raw)
    magento_cat_tree = extract_magento_categories(magento_cat_raw)

    # Also merge any other category files found in the data directory so
    # category IDs referenced by products are more likely to be resolvable.
    try:
        data_dir = Path(DATA_DIR)
        for p in sorted(data_dir.glob("*_categories.json")):
            # Skip the primary file already loaded
            if str(p) == get_magento_cat_file():
                continue
            other_raw = load_json(str(p))
            other_tree = extract_magento_categories(other_raw)
            if other_tree:
                magento_cat_tree.extend(other_tree)
    except Exception:
        # Non-fatal; proceed with whatever tree we have
        pass
    pim_map         = parse_pim_products(pim_raw)
    pim_cat_data    = pim_cat_raw

    print(
        f"\nReady - {len(pim_map):,} PIM SKUs | "
        f"{len(magento_map):,} Magento SKUs | "
        f"{len(id_to_sku):,} ID->SKU mappings\n"
    )

    return {
        "pim_map":         pim_map,
        "pim_cat_data":    pim_cat_data,
        "magento_map":      magento_map,
        "magento_cat_tree": magento_cat_tree,
        "id_to_sku":       id_to_sku,
    }

def _run_hierarchy(ctx: dict) -> None:
    print("Type a SKU to view its hierarchy. Enter 'quit' to go back.\n")
    while True:
        sku = input("SKU > ").strip()
        if not sku or sku.lower() in ("exit", "quit", "q"):
            break
        print(f"\n{'=' * 60}")
        print(f"  PIM HIERARCHY  -  SKU: {sku}")
        print("=" * 60)
        for line in get_pim_hierarchy(sku, ctx["pim_map"], ctx["pim_cat_data"]):
            print(line)
        print(f"\n{'=' * 60}")
        print(f"  MAGENTO HIERARCHY  -  SKU: {sku}")
        print("=" * 60)
        for line in get_magento_hierarchy(sku, ctx["magento_map"], ctx["magento_cat_tree"]):
            print(line)
        print()

def _run_single_compare(ctx: dict) -> None:
    print("Type a SKU to compare. Enter 'quit' to go back.\n")
    while True:
        sku = input("SKU > ").strip()
        if not sku or sku.lower() in ("exit", "quit", "q"):
            break
        report = compare_product(sku, ctx["pim_map"], ctx["magento_map"], ctx["id_to_sku"], ctx.get("magento_cat_tree"))
        print_report(report)

def _run_batch(ctx: dict) -> None:
    print("\nRunning batch comparison ...")
    reports = batch_compare(ctx["pim_map"], ctx["magento_map"], ctx["id_to_sku"], ctx.get("magento_cat_tree"))
    summarize_batch(reports)

def _run_market_counter(ctx: dict) -> None:
    market_index = build_market_index(ctx["pim_map"])
    while True:
        print("\n  Market options:")
        print("    a) List all markets")
        print("    b) Lookup by brand code")
        print("    c) Search by name")
        print("    q) Back to main menu")
        choice = input("\n  Choice > ").strip().lower()
        if choice == "a":
            print_all_markets(list_all_markets(market_index))
        elif choice == "b":
            code   = input("  Brand code (e.g. DL, AC, AX) > ").strip()
            detail = get_market_products(code, market_index, ctx["pim_map"])
            if detail:
                print_market_detail(detail)
            else:
                matches = search_market_by_description(code, market_index)
                if matches:
                    print(f"\n  Code '{code}' not found. Did you mean:")
                    for m in matches:
                        print(f"    - {m['code']:<8} - {m['description']}  ({m['count']} products)")
                else:
                    print(f"\n  Brand code '{code.upper()}' not found in PIM data.")
        elif choice == "c":
            query   = input("  Search term > ").strip()
            matches = search_market_by_description(query, market_index)
            if matches:
                print(f"\n  Found {len(matches)} market(s):")
                for m in sorted(matches, key=lambda x: x["code"]):
                    print(f"    - {m['code']:<8} - {m['description']:<35}  ({m['count']} products)")
            else:
                print(f"  No markets matched '{query}'.")
        elif choice in ("q", "quit", "exit", ""):
            break
        else:
            print("  Unknown option.")

def _run_batch_html(ctx: dict) -> None:
    default = "batch_report.html"
    path    = input(f"\n  Output file path [{default}]: ").strip() or default
    out     = generate_html_report(
        ctx["pim_map"],
        ctx["magento_map"],
        ctx["id_to_sku"],
        output_path=path,
        magento_cat_tree=ctx.get("magento_cat_tree"),
    )
    try:
        import webbrowser
        webbrowser.open(f"file://{os.path.abspath(out)}")
        print("Opened in your default browser.")
    except Exception:
        print(f"Open manually: {os.path.abspath(out)}")

def main():
    ctx = _load_all()

    while True:
        print("\nModes:")
        print("  1) Hierarchy viewer   - PIM + Magento tree for a SKU")
        print("  2) Single compare     - PIM vs Magento for a SKU")
        print("  3) Batch compare      - all PIM SKUs vs Magento (console)")
        print("  4) Market counter     - products per brand/market code")
        print("  5) Batch HTML report  - export full report to HTML file")
        print("  q) Quit")

        mode = input("\nChoose mode (1 / 2 / 3 / 4 / 5 / q): ").strip().lower()

        if mode == "1":
            _run_hierarchy(ctx)
        elif mode == "2":
            _run_single_compare(ctx)
        elif mode == "3":
            _run_batch(ctx)
        elif mode == "4":
            _run_market_counter(ctx)
        elif mode == "5":
            _run_batch_html(ctx)
        elif mode in ("q", "quit", "exit"):
            print("Goodbye!")
            break
        else:
            print("Unknown mode - please enter 1, 2, 3, 4, 5, or q.")

if __name__ == "__main__":
    main()
