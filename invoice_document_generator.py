"""
Invoice Document Generator
=========================

This module generates beautiful HTML invoices from invoice data.
"""

from datetime import datetime
from typing import Dict
from pathlib import Path

import config


class InvoiceDocumentGenerator:
    """Generate invoice documents in HTML format."""
    
    def __init__(self):
        """Initialize the document generator."""
        self.output_dir = Path("generated_invoices")
        self.output_dir.mkdir(exist_ok=True)
        
        # Company colors from our branding
        self.primary_color = "#2E4057"
        self.accent_color = "#048A81" 
        self.secondary_color = "#54C6EB"
        
    def generate_html_invoice(self, invoice_data: Dict) -> str:
        """
        Generate an HTML invoice document.
        
        Args:
            invoice_data (Dict): Invoice data
            
        Returns:
            str: Path to generated HTML file
        """
        try:
            invoice_number = invoice_data.get("invoice_number", "UNKNOWN")
            filename = f"{invoice_number}.html"
            filepath = self.output_dir / filename
            
            html_content = self._create_html_content(invoice_data)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
                
            print(f"✅ HTML invoice generated: {filepath}")
            return str(filepath)
            
        except Exception as e:
            print(f"❌ Error generating HTML invoice: {e}")
            return ""
    
    def _create_html_content(self, invoice_data: Dict) -> str:
        """Create HTML content for invoice."""
        client_data = invoice_data.get("client", {})
        line_items = invoice_data.get("line_items", [])
        
        # Calculate totals
        subtotal = float(invoice_data.get("subtotal", 0))
        tax_rate = float(invoice_data.get("tax_rate", 0))
        tax_amount = float(invoice_data.get("tax_amount", 0))
        total = float(invoice_data.get("total", 0))
        
        # Generate line items HTML
        items_html = ""
        for item in line_items:
            qty = item.get("quantity", 1)
            price = float(item.get("unit_price", 0))
            item_total = qty * price
            
            items_html += f"""
            <tr>
                <td style="padding: 12px; border-bottom: 1px solid #eee;">{item.get('description', 'Service')}</td>
                <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: center;">{qty}</td>
                <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: right;">${price:.2f}</td>
                <td style="padding: 12px; border-bottom: 1px solid #eee; text-align: right; font-weight: bold;">${item_total:.2f}</td>
            </tr>
            """
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Invoice {invoice_data.get('invoice_number', 'N/A')}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: {self.primary_color};
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background: #f8f9fa;
        }}
        .invoice-container {{
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 3px solid {self.accent_color};
        }}
        .company-info {{
            flex: 1;
        }}
        .company-name {{
            font-size: 28px;
            font-weight: bold;
            color: {self.primary_color};
            margin-bottom: 10px;
        }}
        .company-details {{
            color: #666;
            line-height: 1.4;
        }}
        .invoice-title {{
            font-size: 36px;
            font-weight: bold;
            color: {self.accent_color};
            text-align: right;
        }}
        .invoice-meta {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 30px;
        }}
        .invoice-details, .client-details {{
            flex: 1;
            margin-right: 20px;
        }}
        .section-title {{
            font-size: 18px;
            font-weight: bold;
            color: {self.primary_color};
            margin-bottom: 10px;
            padding-bottom: 5px;
            border-bottom: 2px solid {self.secondary_color};
        }}
        .invoice-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 30px 0;
            background: white;
        }}
        .invoice-table th {{
            background: {self.primary_color};
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: bold;
        }}
        .invoice-table th:last-child,
        .invoice-table td:last-child {{
            text-align: right;
        }}
        .invoice-table th:nth-child(2),
        .invoice-table td:nth-child(2) {{
            text-align: center;
        }}
        .totals-section {{
            margin-top: 30px;
            text-align: right;
        }}
        .totals-table {{
            margin-left: auto;
            min-width: 300px;
        }}
        .totals-table td {{
            padding: 8px 15px;
            border-bottom: 1px solid #eee;
        }}
        .total-row {{
            font-size: 20px;
            font-weight: bold;
            background: {self.accent_color};
            color: white;
        }}
        .total-row td {{
            border: none;
            padding: 15px;
        }}
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid {self.secondary_color};
            text-align: center;
            color: #666;
        }}
        .payment-terms {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin-top: 30px;
            border-left: 4px solid {self.accent_color};
        }}
        @media print {{
            body {{ background: white; }}
            .invoice-container {{ box-shadow: none; }}
        }}
    </style>
</head>
<body>
    <div class="invoice-container">
        <!-- Header -->
        <div class="header">
            <div class="company-info">
                <div class="company-name">{config.COMPANY_NAME}</div>
                <div class="company-details">
                    {config.COMPANY_ADDRESS}<br>
                    Phone: {config.COMPANY_PHONE}<br>
                    Email: {config.COMPANY_EMAIL}<br>
                    Website: {config.COMPANY_WEBSITE}
                </div>
            </div>
            <div class="invoice-title">INVOICE</div>
        </div>
        
        <!-- Invoice and Client Details -->
        <div class="invoice-meta">
            <div class="invoice-details">
                <div class="section-title">Invoice Details</div>
                <strong>Invoice Number:</strong> {invoice_data.get('invoice_number', 'N/A')}<br>
                <strong>Invoice Date:</strong> {invoice_data.get('invoice_date', datetime.now().strftime('%m/%d/%Y'))}<br>
                <strong>Due Date:</strong> {invoice_data.get('due_date', 'N/A')}<br>
                <strong>Payment Terms:</strong> {invoice_data.get('payment_terms', 'Net 30')}<br>
                {f"<strong>PO Number:</strong> {invoice_data.get('po_number')}<br>" if invoice_data.get('po_number') else ""}
                {f"<strong>Project Ref:</strong> {invoice_data.get('project_ref')}<br>" if invoice_data.get('project_ref') else ""}
            </div>
            
            <div class="client-details">
                <div class="section-title">Bill To</div>
                <strong>{client_data.get('name', 'Client Name Required')}</strong><br>
                {client_data.get('address', 'Address Required')}<br>
                {f"{client_data.get('contact', '')}<br>" if client_data.get('contact') else ""}
                {f"{client_data.get('email', '')}<br>" if client_data.get('email') else ""}
            </div>
        </div>
        
        <!-- Line Items -->
        <table class="invoice-table">
            <thead>
                <tr>
                    <th>Description</th>
                    <th>Quantity</th>
                    <th>Unit Price</th>
                    <th>Total</th>
                </tr>
            </thead>
            <tbody>
                {items_html}
            </tbody>
        </table>
        
        <!-- Totals -->
        <div class="totals-section">
            <table class="totals-table">
                <tr>
                    <td><strong>Subtotal:</strong></td>
                    <td><strong>${subtotal:.2f}</strong></td>
                </tr>
                <tr>
                    <td><strong>Tax ({tax_rate*100:.1f}%):</strong></td>
                    <td><strong>${tax_amount:.2f}</strong></td>
                </tr>
                <tr class="total-row">
                    <td><strong>TOTAL:</strong></td>
                    <td><strong>${total:.2f} {invoice_data.get('currency', 'USD')}</strong></td>
                </tr>
            </table>
        </div>
        
        <!-- Payment Terms -->
        {f'''<div class="payment-terms">
            <strong>Special Instructions:</strong><br>
            {invoice_data.get('special_instructions', '')}
        </div>''' if invoice_data.get('special_instructions') else ''}
        
        <!-- Footer -->
        <div class="footer">
            <p><strong>Thank you for your business!</strong></p>
            <p>Tax ID: {config.COMPANY_TAX_ID} | Questions? Contact {config.COMPANY_EMAIL}</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html_template


def test_document_generator():
    """Test the document generator with sample data."""
    generator = InvoiceDocumentGenerator()
    
    # Sample invoice data
    sample_invoice = {
        "invoice_number": f"DEMO-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "invoice_date": "12/01/2024",
        "due_date": "12/31/2024",
        "client": {
            "name": "Acme Corporation",
            "address": "456 Business Avenue, Suite 200, Corporate City, CC 67890",
            "contact": "John Smith, Procurement Manager",
            "email": "john.smith@acmecorp.com"
        },
        "line_items": [
            {
                "description": "Web Design and Development Services",
                "quantity": 40,
                "unit_price": 125.00,
            },
            {
                "description": "Content Management System Setup",
                "quantity": 1,
                "unit_price": 800.00,
            },
            {
                "description": "SEO Optimization Package",
                "quantity": 1,
                "unit_price": 500.00,
            },
        ],
        "subtotal": 6300.00,
        "tax_rate": 0.08,
        "tax_amount": 504.00,
        "total": 6804.00,
        "currency": "USD",
        "payment_terms": "Net 30",
        "po_number": "PO-2024-12345",
        "project_ref": "Website Redesign Project",
        "special_instructions": "Please process payment within 30 days. Contact billing@professionalservices.com for any questions."
    }
    
    print("🧪 Testing Invoice Document Generator")
    print("=" * 50)
    
    # Generate HTML invoice
    result = generator.generate_html_invoice(sample_invoice)
    
    print(f"\n📄 Generated HTML file: {result}")
    
    return result


if __name__ == "__main__":
    test_document_generator()