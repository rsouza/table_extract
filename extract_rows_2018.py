from rows.plugins.plugin_pdf import (
    PyMuPDFTesseractBackend,
    TextObject,
    YGroupsAlgorithm,
    group_objects,
)


def extract_rows(filename):
    doc = PyMuPDFTesseractBackend(filename)
    x_intervals = None
    header = "Municipios,Nome do Conflito,Familias,Area".split(",")
    for index, page in enumerate(doc.objects()):
        if index == 0:
            page = page[1:]  # Skip title object
        grouped = group_objects("y", page)
        text_page = []
        for group in page:
            text_page.append(
                TextObject(
                    x0=group.x0, x1=group.x1, y0=group.y0, y1=group.y1, text=group.text
                )
            )
        extractor = YGroupsAlgorithm(text_page)
        if index == 0:
            x_intervals = extractor.x_intervals
        else:
            extractor.x_intervals = x_intervals
        lines = extractor.get_lines()
        final_lines = []
        for line in lines:
            new_line = []
            for cell in line:
                value = " ".join(obj.text for obj in cell) if cell is not None else None
                new_line.append(value)
            final_lines.append(new_line)
        for line in final_lines:
            if line == header:
                continue
            yield dict(zip(header, line))


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
