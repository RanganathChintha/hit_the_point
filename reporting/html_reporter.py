# reporting/html_reporter.py

from __future__ import annotations
import datetime

def _has_issues(report: dict) -> bool:
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

def _issue_categories(report: dict) -> list:
    cats = []
    if not report["found_in_magento"]:
        cats.append("Missing in Magento")
        return cats
    tc = report.get("type_comparison")
    if tc and not tc["types_match"]:
        cats.append("Type Mismatch")
    bc = report.get("bundle_comparison")
    if bc:
        if not bc["slot_count_match"] or bc["slots_only_in_pim"] or bc["slots_only_in_magento"]:
            cats.append("Bundle Slot Issue")
        if any(
            not sd["count_match"] or sd["skus_only_in_pim"] or sd["skus_only_in_magento"]
            for sd in bc["per_slot"].values()
        ):
            cats.append("Bundle SKU Issue")
    cc = report.get("configurable_comparison")
    if cc and (not cc["count_match"] or cc["skus_only_in_pim"] or cc["skus_only_in_magento"]):
        cats.append("Configurable Child Issue")
    catc = report.get("category_comparison")
    if catc and not catc["matches"]:
        cats.append("Category Link Issue")
    return cats

_CSS = """
    :root {
        --ok:      #16a34a;
        --err:     #dc2626;
        --warn:    #d97706;
        --info:    #2563eb;
        --bg:      #f8fafc;
        --card:    #ffffff;
        --border:  #e2e8f0;
        --text:    #1e293b;
        --muted:   #64748b;
        --radius:  8px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', system-ui, sans-serif; background: var(--bg); color: var(--text); font-size: 14px; line-height: 1.5; }
    header { background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%); color: #fff; padding: 24px 32px; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 12px; }
    header h1 { font-size: 22px; font-weight: 700; letter-spacing: .3px; }
    header .meta { font-size: 12px; opacity: .8; }
    .summary-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; padding: 24px 32px 0; }
    .card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 18px 20px; text-align: center; }
    .card .num { font-size: 32px; font-weight: 700; }
    .card .lbl { font-size: 12px; color: var(--muted); margin-top: 4px; }
    .card.ok .num { color: var(--ok); }
    .card.err .num { color: var(--err); }
    .card.warn .num { color: var(--warn); }
    .card.info .num { color: var(--info); }
    .toolbar { padding: 20px 32px; display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
    .toolbar input { flex: 1; min-width: 220px; padding: 8px 12px; border: 1px solid var(--border); border-radius: var(--radius); font-size: 13px; outline: none; }
    .toolbar input:focus { border-color: #2563eb; box-shadow: 0 0 0 3px #dbeafe; }
    .toolbar select { padding: 8px 12px; border: 1px solid var(--border); border-radius: var(--radius); font-size: 13px; background: var(--card); cursor: pointer; }
    .btn-export { padding: 8px 16px; background: #2563eb; color: #fff; border: none; border-radius: var(--radius); font-size: 13px; cursor: pointer; font-weight: 600; }
    .btn-export:hover { background: #1d4ed8; }
    .table-wrap { padding: 0 32px 40px; overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; }
    thead th { background: #f1f5f9; padding: 10px 14px; text-align: left; font-size: 12px; font-weight: 600; color: var(--muted); text-transform: uppercase; letter-spacing: .5px; border-bottom: 1px solid var(--border); cursor: pointer; user-select: none; white-space: nowrap; }
    thead th:hover { background: #e2e8f0; }
    thead th .sort-icon { margin-left: 4px; opacity: .4; }
    thead th.sorted .sort-icon { opacity: 1; }
    tbody tr { border-bottom: 1px solid var(--border); transition: background .1s; }
    tbody tr:last-child { border-bottom: none; }
    tbody tr:hover { background: #f8fafc; }
    tbody td { padding: 10px 14px; vertical-align: top; }
    .badge { display: inline-block; padding: 2px 8px; border-radius: 99px; font-size: 11px; font-weight: 600; white-space: nowrap; }
    .badge-ok { background: #dcfce7; color: #166534; }
    .badge-err { background: #fee2e2; color: #991b1b; }
    .badge-warn { background: #fef9c3; color: #854d0e; }
    .badge-info { background: #dbeafe; color: #1e40af; }
    .badge-ptype { background: #f3e8ff; color: #6b21a8; }
    .badge-ftype { background: #e0f2fe; color: #0c4a6e; }
    .detail-row td { padding: 0; background: #f8fafc; }
    .detail-inner { padding: 16px 24px; border-top: 1px dashed var(--border); display: none; }
    .detail-inner.open { display: block; }
    .detail-section { margin-bottom: 14px; }
    .detail-section h4 { font-size: 12px; font-weight: 700; color: var(--muted); text-transform: uppercase; letter-spacing: .5px; margin-bottom: 8px; }
    .sku-list { display: flex; flex-wrap: wrap; gap: 6px; }
    .sku-chip { background: #f1f5f9; border: 1px solid var(--border); border-radius: 4px; padding: 2px 8px; font-size: 12px; font-family: monospace; }
    .sku-chip.missing { background: #fee2e2; border-color: #fca5a5; }
    .sku-chip.extra { background: #dbeafe; border-color: #93c5fd; }
    .btn-expand { background: none; border: 1px solid var(--border); border-radius: 4px; padding: 2px 8px; cursor: pointer; font-size: 12px; color: var(--muted); }
    .btn-expand:hover { background: #f1f5f9; }
    .pagination { padding: 0 32px 32px; display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
    .pagination button { padding: 6px 12px; border: 1px solid var(--border); border-radius: var(--radius); background: var(--card); cursor: pointer; font-size: 13px; }
    .pagination button.active { background: #2563eb; color: #fff; border-color: #2563eb; }
    .pagination button:hover:not(.active) { background: #f1f5f9; }
    .pagination .page-info { color: var(--muted); font-size: 13px; }
"""

_JS = r"""
(function () {
    const RAW = window.__REPORT_DATA__;
    let filtered = [...RAW];
    let sortCol = null;
    let sortDir = 1;
    let page = 1;
    const PAGE_SZ = 50;
    const tbody    = document.getElementById('tbody');
    const pgBox    = document.getElementById('pagination');
    const searchEl = document.getElementById('search');
    const filterEl = document.getElementById('filter');
    const countEl  = document.getElementById('row-count');

    function applyFilter() {
        const q   = searchEl.value.trim().toLowerCase();
        const cat = filterEl.value;
        filtered = RAW.filter(r => {
            const matchQ   = !q || r.sku.toLowerCase().includes(q) || (r.name||'').toLowerCase().includes(q);
            const matchCat = cat === 'all' ? true : cat === 'ok' ? !r.has_issues : r.issue_cats.includes(cat);
            return matchQ && matchCat;
        });
        page = 1;
        if (sortCol !== null) applySort(false);
        render();
    }

    function applySort(reRender = true) {
        filtered.sort((a, b) => {
            let va = a[sortCol] ?? '';
            let vb = b[sortCol] ?? '';
            if (typeof va === 'string') va = va.toLowerCase();
            if (typeof vb === 'string') vb = vb.toLowerCase();
            return va < vb ? -sortDir : va > vb ? sortDir : 0;
        });
        if (reRender) render();
    }

    document.querySelectorAll('thead th[data-col]').forEach(th => {
        th.addEventListener('click', () => {
            const col = th.dataset.col;
            if (sortCol === col) { sortDir *= -1; } else { sortCol = col; sortDir = 1; }
            document.querySelectorAll('thead th').forEach(t => {
                t.classList.remove('sorted');
                t.querySelector('.sort-icon').textContent = '⇅';
            });
            th.classList.add('sorted');
            th.querySelector('.sort-icon').textContent = sortDir === 1 ? '↑' : '↓';
            applySort();
        });
    });

    function statusBadge(r) {
        if (!r.has_issues) return '<span class="badge badge-ok">✅ OK</span>';
        return r.issue_cats.map(c => {
            const cls = c === 'Missing in Magento' ? 'badge-err'
                      : c.includes('Mismatch')    ? 'badge-warn'
                      : 'badge-info';
            return `<span class="badge ${cls}">${c}</span>`;
        }).join(' ');
    }

    function detailHtml(r) {
        let html = '';

        const foundBadge = r.found_in_magento
            ? '<span class="badge badge-ok">✅ Found in Magento</span>'
            : '<span class="badge badge-err">❌ Missing in Magento</span>';
        html += `<div class="detail-section"><h4>Availability</h4>${foundBadge}</div>`;

        if (r.type_comparison) {
            const tc = r.type_comparison;
            html += `<div class="detail-section"><h4>Type Comparison</h4>
                <span class="badge badge-ptype">PIM: ${tc.pim_type}</span>
                &nbsp;&rarr;&nbsp;
                <span class="badge badge-ftype">Magento: ${tc.magento_type}</span>&nbsp;`;
            html += tc.types_match
                ? '<span class="badge badge-ok">✅ Match</span>'
                : '<span class="badge badge-err">❌ Mismatch</span>';
            html += '</div>';
        }

        if (r.bundle_comparison) {
            const bc = r.bundle_comparison;
            html += `<div class="detail-section"><h4>Bundle Slots</h4>
                <p>PIM slots: <b>${bc.pim_slot_count}</b> &nbsp;|&nbsp; Magento slots: <b>${bc.magento_slot_count}</b>
                &nbsp;${bc.slot_count_match
                    ? '<span class="badge badge-ok">✅ Match</span>'
                    : '<span class="badge badge-err">❌ Mismatch</span>'}</p>`;
            if (bc.slots_only_in_pim.length)
                html += `<p style="margin-top:6px">❌ Missing in Magento:
                    <span class="sku-list">${bc.slots_only_in_pim.map(s=>`<span class="sku-chip missing">${s}</span>`).join('')}</span></p>`;
            if (bc.slots_only_in_magento.length)
                html += `<p style="margin-top:6px">ℹ️ Extra in Magento:
                    <span class="sku-list">${bc.slots_only_in_magento.map(s=>`<span class="sku-chip extra">${s}</span>`).join('')}</span></p>`;
            for (const [slot, sd] of Object.entries(bc.per_slot)) {
                html += `<div style="margin-top:10px;padding:8px 12px;border:1px solid var(--border);border-radius:6px;background:#fff">
                    <b style="font-size:12px">[${slot.toUpperCase()}]</b>
                    &nbsp; PIM: <b>${sd.pim_sku_count}</b> &nbsp;|&nbsp; Magento: <b>${sd.magento_sku_count}</b>
                    &nbsp;${sd.count_match
                        ? '<span class="badge badge-ok">✅ Match</span>'
                        : '<span class="badge badge-err">❌ Mismatch</span>'}`;
                if (sd.skus_only_in_pim.length)
                    html += `<div style="margin-top:6px">❌ Missing in Magento:
                        <div class="sku-list" style="margin-top:4px">${sd.skus_only_in_pim.map(s=>`<span class="sku-chip missing">${s}</span>`).join('')}</div></div>`;
                if (sd.skus_only_in_magento.length)
                    html += `<div style="margin-top:6px">ℹ️ Extra in Magento:
                        <div class="sku-list" style="margin-top:4px">${sd.skus_only_in_magento.map(s=>`<span class="sku-chip extra">${s}</span>`).join('')}</div></div>`;
                if (sd.count_match && !sd.skus_only_in_pim.length && !sd.skus_only_in_magento.length)
                    html += `<div style="margin-top:6px"><span class="badge badge-ok">✅ All children match</span></div>`;
                html += '</div>';
            }
            html += '</div>';
        }

        if (r.configurable_comparison) {
            const cc = r.configurable_comparison;
            html += `<div class="detail-section"><h4>Configurable Children</h4>
                <p>PIM: <b>${cc.pim_child_count}</b> &nbsp;|&nbsp; Magento: <b>${cc.magento_child_count}</b>
                &nbsp;${cc.count_match
                    ? '<span class="badge badge-ok">✅ Match</span>'
                    : '<span class="badge badge-err">❌ Mismatch</span>'}</p>`;
            if (cc.skus_only_in_pim.length)
                html += `<div style="margin-top:6px">❌ Missing in Magento:
                    <div class="sku-list" style="margin-top:4px">${cc.skus_only_in_pim.map(s=>`<span class="sku-chip missing">${s}</span>`).join('')}</div></div>`;
            if (cc.skus_only_in_magento.length)
                html += `<div style="margin-top:6px">ℹ️ Extra in Magento:
                    <div class="sku-list" style="margin-top:4px">${cc.skus_only_in_magento.map(s=>`<span class="sku-chip extra">${s}</span>`).join('')}</div></div>`;
            if (cc.unresolved_magento_ids && cc.unresolved_magento_ids.length)
                html += `<p style="margin-top:6px">⚠️ Unresolved Magento IDs: ${cc.unresolved_magento_ids.join(', ')}</p>`;
            if (cc.count_match && !cc.skus_only_in_pim.length && !cc.skus_only_in_magento.length)
                html += `<div style="margin-top:6px"><span class="badge badge-ok">✅ All children match</span></div>`;
            html += '</div>';
        }

        if (r.category_comparison) {
            const cat = r.category_comparison;
            html += `<div class="detail-section"><h4>Category Links</h4>
                <p>PIM categories: <b>${(cat.pim_category_ids || []).join(', ') || '—'}</b></p>
                <p>Magento links: <b>${(cat.magento_category_ids || []).join(', ') || '—'}</b></p>
                <p>${cat.matches ? '<span class="badge badge-ok">✅ Match</span>' : '<span class="badge badge-err">❌ Mismatch</span>'}</p>`;
            if (cat.missing_in_magento && cat.missing_in_magento.length)
                html += `<div style="margin-top:6px">❌ Missing in Magento: <span class="sku-list">${cat.missing_in_magento.map(s=>`<span class="sku-chip missing">${s}</span>`).join('')}</span></div>`;
            if (cat.extra_in_magento && cat.extra_in_magento.length)
                html += `<div style="margin-top:6px">ℹ️ Extra in Magento: <span class="sku-list">${cat.extra_in_magento.map(s=>`<span class="sku-chip extra">${s}</span>`).join('')}</span></div>`;
            if (cat.position_mismatches && cat.position_mismatches.length)
                html += `<div style="margin-top:6px">⚠️ Position mismatches: <span class="sku-list">${cat.position_mismatches.map(x=>`<span class="sku-chip">${x.category_id} (${x.expected_position}→${x.actual_position})</span>`).join('')}</span></div>`;
            if (cat.unknown_categories && cat.unknown_categories.length)
                html += `<div style="margin-top:6px">⚠️ Unknown category IDs: <span class="sku-list">${cat.unknown_categories.map(s=>`<span class="sku-chip">${s}</span>`).join('')}</span></div>`;
            html += '</div>';
        }

        if (!r.type_comparison && !r.bundle_comparison && !r.configurable_comparison && !r.category_comparison) {
            html += `<div class="detail-section"><h4>Summary</h4>
                <span class="badge badge-ok">✅ Found in Magento — no structural comparison available for this type</span>
            </div>`;
        }

        return html;
    }

    function render() {
        const start = (page - 1) * PAGE_SZ;
        const slice = filtered.slice(start, start + PAGE_SZ);
        countEl.textContent = `Showing ${filtered.length} of ${RAW.length} SKUs`;
        tbody.innerHTML = slice.map((r, i) => {
            const detId = `det-${start + i}`;
            return `
            <tr>
                <td><code style="font-size:12px">${r.sku}</code></td>
                <td style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap"
                    title="${(r.name||'').replace(/"/g,'"')}">${r.name || '&#8212;'}</td>
                <td><span class="badge badge-ptype">${r.pim_type}</span></td>
                <td><span class="badge badge-ftype">${r.magento_type}</span></td>
                <td>${statusBadge(r)}</td>
                <td><button class="btn-expand" onclick="toggleDetail('${detId}', this)">&#9654; Details</button></td>
            </tr>
            <tr class="detail-row">
                <td colspan="6">
                    <div class="detail-inner" id="${detId}">${detailHtml(r)}</div>
                </td>
            </tr>`;
        }).join('');
        renderPagination();
    }

    window.toggleDetail = function(detId, btn) {
        const el   = document.getElementById(detId);
        const open = el.classList.toggle('open');
        btn.textContent = open ? '▼ Details' : '► Details';
    };

    function renderPagination() {
        const total = Math.ceil(filtered.length / PAGE_SZ);
        if (total <= 1) { pgBox.innerHTML = ''; return; }
        let html = `<span class="page-info">Page ${page} of ${total}</span>`;
        html += `<button ${page===1?'disabled':''} onclick="goPage(${page-1})">&#8249; Prev</button>`;
        for (let p = 1; p <= total; p++) {
            if (total > 10 && Math.abs(p - page) > 2 && p !== 1 && p !== total) {
                if (p === 2 || p === total - 1) html += '<span style="padding:0 4px">&hellip;</span>';
                continue;
            }
            html += `<button class="${p===page?'active':''}" onclick="goPage(${p})">${p}</button>`;
        }
        html += `<button ${page===total?'disabled':''} onclick="goPage(${page+1})">Next &#8250;</button>`;
        pgBox.innerHTML = html;
    }

    window.goPage = function(p) { page = p; render(); window.scrollTo(0, 0); };

    window.exportCSV = function() {
        const cols = ['sku','name','pim_type','magento_type','has_issues','issue_cats'];
        const rows = [cols.join(',')];
        filtered.forEach(r => {
            rows.push([
                `"${r.sku}"`,
                `"${(r.name||'').replace(/"/g,'""')}"`,
                r.pim_type,
                r.magento_type,
                r.has_issues,
                `"${r.issue_cats.join('; ')}"`,
            ].join(','));
        });
        const blob = new Blob([rows.join('\n')], { type: 'text/csv' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = 'pim_magento_report.csv';
        a.click();
    };

    searchEl.addEventListener('input', applyFilter);
    filterEl.addEventListener('change', applyFilter);
    applyFilter();
})();
"""

def _build_row(report: dict, pim_map: dict, magento_map: dict) -> dict:
    sku          = report["sku"]
    pim_entry    = pim_map.get(sku, {})
    magento_entry = magento_map.get(sku, {})
    tc           = report.get("type_comparison") or {}
    return {
        "sku":                     sku,
        "name":                    pim_entry.get("name", ""),
        "pim_type":                tc.get("pim_type", pim_entry.get("product_type", "?")),
        "magento_type":             tc.get("magento_type", magento_entry.get("type_id", "NOT FOUND")),
        "has_issues":              _has_issues(report),
        "issue_cats":              _issue_categories(report),
        "markets":                 sorted({
                                       (cl.get("code") or "").strip().upper()
                                       for cl in pim_entry.get("customer_labels", [])
                                       if cl.get("code")
                                   }),
        "found_in_magento":         report["found_in_magento"],
        "type_comparison":         report.get("type_comparison"),
        "bundle_comparison":       report.get("bundle_comparison"),
        "configurable_comparison": report.get("configurable_comparison"),
        "category_comparison":     report.get("category_comparison"),
    }

def generate_html_report(
    pim_map:     dict,
    magento_map:  dict,
    id_to_sku:   dict,
    output_path: str = "batch_report.html",
    magento_cat_tree: list | None = None,
) -> str:
    import json as _json
    from comparison.orchestrator import batch_compare

    print("Running batch comparison ...")
    reports = batch_compare(pim_map, magento_map, id_to_sku, magento_cat_tree)

    total        = len(reports)
    perfect      = sum(1 for r in reports if not _has_issues(r))
    missing      = sum(1 for r in reports if not r["found_in_magento"])
    type_mm      = sum(1 for r in reports if r.get("type_comparison") and not r["type_comparison"]["types_match"])
    bundle_iss   = sum(1 for r in reports if _has_issues(r) and r.get("bundle_comparison"))
    config_iss   = sum(1 for r in reports if _has_issues(r) and r.get("configurable_comparison"))
    category_iss = sum(1 for r in reports if _has_issues(r) and r.get("category_comparison") and not r["category_comparison"]["matches"])
    total_issues = total - perfect

    rows      = [_build_row(r, pim_map, magento_map) for r in reports]

    # Add rows for SKUs in Magento but not in PIM (Missing in PIM)
    pim_skus = set(pim_map)
    magento_skus = set(magento_map)
    missing_in_pim_skus = magento_skus - pim_skus
    missing_in_pim = len(missing_in_pim_skus)
    for sku in missing_in_pim_skus:
        magento_entry = magento_map.get(sku, {})
        row = {
            "sku": sku,
            "name": magento_entry.get("name", ""),
            "pim_type": "NOT IN PIM",
            "magento_type": magento_entry.get("type_id", "?"),
            "has_issues": True,
            "issue_cats": ["Missing in PIM"],
            "markets": [],
            "found_in_magento": True,
            "type_comparison": None,
            "bundle_comparison": None,
            "configurable_comparison": None,
        }
        rows.append(row)

    rows_json = _json.dumps(rows, ensure_ascii=False)

    all_cats = set()
    for r in rows:
        all_cats.update(r["issue_cats"])
    # "Missing in Magento" and "Missing in PIM" are already in issue_cats from the rows
    # No need to add them again as special categories
    filter_options = "".join(f'<option value="{c}">{c}</option>' for c in sorted(all_cats))
    generated_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>PIM vs Magento - Batch Report</title>
<style>{_CSS}</style>
</head>
<body>
<header>
  <div>
    <h1>PIM vs Magento - Batch Comparison Report</h1>
    <div class="meta">Generated: {generated_at}</div>
  </div>
  <div class="meta" style="text-align:right">Total SKUs: <b style="font-size:16px">{total:,}</b></div>
</header>
<div class="summary-grid">
  <div class="card ok"><div class="num">{perfect:,}</div><div class="lbl">Perfect Matches</div></div>
  <div class="card err"><div class="num">{total_issues:,}</div><div class="lbl">Total Issues</div></div>
  <div class="card err"><div class="num">{missing:,}</div><div class="lbl">Missing in Magento</div></div>
  <div class="card err"><div class="num">{missing_in_pim:,}</div><div class="lbl">Missing in PIM</div></div>
  <div class="card warn"><div class="num">{type_mm:,}</div><div class="lbl">Type Mismatches</div></div>
  <div class="card info"><div class="num">{bundle_iss:,}</div><div class="lbl">Bundle Issues</div></div>
  <div class="card info"><div class="num">{config_iss:,}</div><div class="lbl">Configurable Issues</div></div>
  <div class="card info"><div class="num">{category_iss:,}</div><div class="lbl">Category Link Issues</div></div>
</div>
<div class="toolbar">
  <input id="search" type="text" placeholder="Search by SKU or name ..."/>
  <select id="filter">
    <option value="all">All SKUs</option>
    <option value="ok">OK only</option>
    {filter_options}
  </select>
  <button class="btn-export" onclick="exportCSV()">Export CSV</button>
  <span id="row-count" style="color:var(--muted);font-size:13px"></span>
</div>
<div class="table-wrap">
  <table>
    <thead>
      <tr>
        <th data-col="sku">SKU <span class="sort-icon">&#8645;</span></th>
        <th data-col="name">Name <span class="sort-icon">&#8645;</span></th>
        <th data-col="pim_type">PIM Type <span class="sort-icon">&#8645;</span></th>
        <th data-col="magento_type">Magento Type <span class="sort-icon">&#8645;</span></th>
        <th data-col="has_issues">Status <span class="sort-icon">&#8645;</span></th>
        <th>Detail</th>
      </tr>
    </thead>
    <tbody id="tbody"></tbody>
  </table>
</div>
<div class="pagination" id="pagination"></div>
<script>
window.__REPORT_DATA__ = {rows_json};
{_JS}
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"HTML report saved -> {output_path}")
    return output_path