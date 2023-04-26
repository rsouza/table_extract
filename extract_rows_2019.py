# pip install cached-property pdfminer.six https://github.com/turicas/rows/archive/develop.zip
from rows.plugins.plugin_pdf import (
    RectObject,
    TextObject,
    PDFMinerBackend,
    YGroupsAlgorithm,
    split_object_lines,
)


def extract_rows(filename):
    header = "uf municipio nome_conflito familias area".split()
    x_intervals, uf = None, None
    doc = PDFMinerBackend(filename)
    for page in doc.objects():
        page_split = []
        rects_y0 = []
        for obj in page:
            if isinstance(obj, TextObject):
                page_split.extend(split_object_lines(obj))
            elif isinstance(obj, RectObject):
                if obj.y1 - obj.y0 < 700:
                    rects_y0.append(obj.y0)
            else:
                page_split.append(obj)
        y_intervals = [(a, b) for a, b in zip(rects_y0, rects_y0[1:])]
        extractor = YGroupsAlgorithm(
            page_split, y_threshold=0.5, x_threshold=0.5, filtered=True
        )
        extractor.y_intervals = y_intervals
        if x_intervals is None:  # First page, save column positions
            x_intervals = extractor.x_intervals
        else:  # Other pages, force first page's column positions
            extractor.x_intervals = x_intervals
        for line in extractor.get_lines():
            if line[1:4] == [None, None, None]:
                uf = line[0][0].text
                continue
            parts = [
                " ".join(item.text for item in part if item is not None)
                if part
                else None
                for part in line
            ]
            if parts[0] in ("Municípios", "ID Municípios"):  # header, skip
                continue
            row = dict(zip(header, [uf] + parts))
            if row["area"] is None and " " in (row["familias"] or ""):
                row["familias"], row["area"] = row["familias"].split()
            yield row


if __name__ == "__main__":
    import argparse

    from rows.utils import CsvLazyDictWriter
    from tqdm import tqdm

    parser = argparse.ArgumentParser()
    parser.add_argument("input_filename")
    parser.add_argument("output_filename")
    args = parser.parse_args()

    writer = CsvLazyDictWriter(args.output_filename)
    for row in tqdm(extract_rows(args.input_filename)):
        writer.writerow(row)
    writer.close()
