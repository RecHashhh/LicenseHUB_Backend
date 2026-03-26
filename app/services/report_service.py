from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_pdf_report(title: str, rows: list[list[str]], summary: dict[str, int]) -> bytes:
    buffer = BytesIO()
    document = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    content = [
        Paragraph("RIPCONCIV - Gestion de Licencias Autodesk", styles["Title"]),
        Spacer(1, 8),
        Paragraph(title, styles["Heading2"]),
        Spacer(1, 12),
    ]

    table_data = [["Software", "Usuario", "Equipo", "Estado", "Inicio", "Fin"]]
    table_data.extend(rows)

    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f766e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.whitesmoke, colors.lightgrey]),
            ]
        )
    )

    content.append(table)
    content.append(Spacer(1, 16))
    content.append(
        Paragraph(
            (
                f"Totales: {summary['total']} | Activas: {summary['active']} | "
                f"Vencidas: {summary['expired']} | Proximas: {summary['expiring']}"
            ),
            styles["Normal"],
        )
    )

    document.build(content)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes
