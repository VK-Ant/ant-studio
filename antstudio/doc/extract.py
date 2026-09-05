"""Document extraction with pipeline tracking."""
import re
from typing import List, Optional
from antstudio.backbone import Backbone
from antstudio.pipeline import Pipeline
from antstudio.io.reader import read_input
from antstudio.io.writer import Results
from antstudio.doc.loader import load_text

def run(source: str = "", fields: Optional[List[str]] = None, model: str = "default",
        ocr: bool = False, engine: str = "tesseract", schema: str = "",
        db: str = "", query: str = "", url: str = "",
        output: str = "", output_db: str = "", table: str = "results",
        threshold: float = 0.7, verbose: bool = True, **kwargs) -> Results:

    if fields is None:
        fields = ["vendor", "date", "amount", "invoice_number"]

    bb = Backbone(f"doc extract {source}")
    bb.start()

    pipe = Pipeline(f"Document Extraction: {source}")
    pipe.start()

    if verbose:
        print(f"\n  Ant Studio v0.1.0 | DocQWise + llmevalkit + AntGuard\n")

    # Step 1: Read input
    s1 = pipe.add_step("Scan Input", "file_input", {"source": source, "extensions": kwargs.get("extensions", ".pdf,.docx,.txt")})
    s1.start()
    items = read_input(source=source, db=db, query=query, url=url,
                       extensions=kwargs.pop("extensions", ".pdf,.docx,.txt,.doc,.xlsx,.csv,.png,.jpg,.jpeg,.bmp,.tiff"))
    if not items:
        s1.fail(f"No files found: {source}")
        pipe.finish()
        if verbose: pipe.print_status()
        return Results([], audit=bb.finish())
    s1.succeed({"file_count": len(items)}, f"{len(items)} files found")
    if verbose:
        print(f"  [1/4] Scanning {'.' * 20} {len(items)} files found")

    # Step 2: Extract
    s2 = pipe.add_step("Extract Fields", "docqwise_extract", {"fields": fields, "model": model, "ocr": ocr})
    s2.start()
    all_rows = []
    for i, (fname, raw, fpath) in enumerate(items):
        text = load_text(raw, fname)
        if not text or text.startswith("["):
            all_rows.append({"_source": fname, "_error": text or "empty", "_confidence": 0, "_threshold": threshold})
            continue
        extracted = _extract_docqwise(text, fields, model)
        if not extracted:
            extracted = _extract_regex(text, fields)
        row = {"_source": fname, "_path": fpath}
        row.update(extracted.get("fields", {}))
        row["_confidence"] = extracted.get("confidence", 0.0)
        row["_threshold"] = threshold
        field_text = " ".join(str(v) for v in extracted.get("fields", {}).values() if v)
        q = bb.evaluate(fname, field_text, text[:500])
        all_rows.append(row)
    s2.succeed({"rows": len(all_rows)}, f"{len(all_rows)}/{len(items)} complete")
    if verbose:
        print(f"  [2/4] Extracting {'.' * 18} {len(all_rows)}/{len(items)} complete")

    # Step 3: Quality
    s3 = pipe.add_step("Quality Check", "llmevalkit", {"threshold": threshold})
    s3.start()
    passed = sum(1 for r in all_rows if r.get("_confidence", 0) >= threshold)
    flagged = len(all_rows) - passed
    s3.quality_score = {"score": passed / max(len(all_rows), 1), "passed": flagged == 0}
    s3.succeed({"passed": passed, "flagged": flagged}, f"{passed} passed, {flagged} flagged")
    if verbose:
        print(f"  [3/4] Quality (llmevalkit) {'.' * 10} {passed} passed, {flagged} flagged")

    # Step 4: Privacy audit
    s4 = pipe.add_step("Privacy Audit", "antguard", {})
    s4.start()
    audit = bb.finish()
    dl = audit["privacy"]["data_left_system"]
    risk = audit["privacy"]["risk_level"]
    s4.succeed({"data_left": dl, "risk": risk}, f"data_left: {'YES' if dl else 'NO'} | risk: {risk}")
    if verbose:
        print(f"  [4/4] Privacy (AntGuard) {'.' * 11} data_left: {'YES' if dl else 'NO'} | risk: {risk}")

    pipe.finish()
    results = Results(all_rows, quality=bb.quality_scores, audit=audit)

    # Output
    if output:
        # Step 5: Save output
        s5 = pipe.add_step("Save Output", "export", {"path": output})
        s5.start()
        results.save(output)
        s5.succeed({"path": output, "rows": results.count})
        if verbose: print(f"\n  Results saved: {output} ({results.count} rows)")

    if output_db:
        results.to_database(output_db, table=table)

    if flagged > 0 and output:
        flagged_path = output.replace(".", "_flagged.")
        results.flagged.save(flagged_path)
        if verbose: print(f"  Flagged items: {flagged_path} ({flagged} rows)")

    # Save quality + audit reports
    if output:
        try:
            from antstudio.reports import save_reports
            extra = {"source": source, "fields": ", ".join(fields or []),
                     "files_processed": len(items), "passed": passed, "flagged": flagged}
            report_paths = save_reports(
                bb.quality_scores, audit, output,
                pipeline_name=pipe.name, run_id=pipe.run_id, extra_info=extra
            )
            if verbose:
                for rtype, rpath in report_paths.items():
                    print(f"  Report ({rtype}): {rpath}")
        except Exception:
            pass

    # Print pipeline view
    if verbose:
        pipe.print_status()

    return results


def _extract_docqwise(text, fields, model):
    try:
        from docqwise import DocQWise
        dq = DocQWise(model=model)
        result = dq.extract(text, fields=fields)
        return {"fields": result.fields, "confidence": result.confidence}
    except ImportError:
        return {}
    except Exception:
        return {}

def _extract_regex(text, fields):
    extracted = {}
    patterns = {
        "vendor": [r"(?:vendor|supplier|from|company)[:\s]+([A-Z][A-Za-z\s&.,]+?)(?:\n|$)", r"^([A-Z][A-Z\s&.,]{3,30})\s*(?:LLC|Inc|Corp|Ltd)?"],
        "date": [r"(?:date|dated|invoice date)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"],
        "amount": [r"(?:total|amount|balance|due)[:\s]*\$?([\d,]+\.?\d*)", r"\$\s*([\d,]+\.?\d*)"],
        "invoice_number": [r"(?:invoice|inv|invoice no|invoice #)[:\s#]*([A-Za-z0-9-]+)"],
        "gst": [r"(?:gst|gstin|tax id)[:\s]*([A-Z0-9]{10,20})"],
        "due_date": [r"(?:due date|payment due|due)[:\s]+(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"],
    }
    found = 0
    for field in fields:
        key = field.strip().lower().replace(" ", "_")
        for pk, pats in patterns.items():
            if key == pk or key.replace("_", "") == pk.replace("_", ""):
                for pat in pats:
                    m = re.search(pat, text, re.IGNORECASE | re.MULTILINE)
                    if m:
                        extracted[field.strip()] = m.group(1).strip()
                        found += 1
                        break
                break
        if field.strip() not in extracted:
            extracted[field.strip()] = ""
    return {"fields": extracted, "confidence": round(found / max(len(fields), 1), 3)}
