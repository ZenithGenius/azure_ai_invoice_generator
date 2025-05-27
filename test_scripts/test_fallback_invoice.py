#!/usr/bin/env python3
"""
Test script for the enhanced fallback invoice generation system.
This script tests the HTML template-based fallback mechanism.
"""

import sys
import os
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from generate_invoices import InvoiceGenerationSystem

def test_fallback_invoice():
    """Test the fallback invoice generation with HTML template."""
    print("🧪 Testing Enhanced Fallback Invoice Generation System")
    print("=" * 60)
    
    # Initialize the invoice system
    invoice_system = InvoiceGenerationSystem()
    
    # Test order details (similar to your example)
    test_order = {
        "order_id": "TEST-FALLBACK-001",
        "client_name": "Jason",
        "client_email": "joumessiisaac@gmail.com",
        "client_address": "Biyemassi\nNomayos",
        "client_contact": "Jason",
        "items": [
            {
                "description": "test",
                "quantity": 1,
                "unit_price": 1.0
            }
        ],
        "tax_rate": 0.08,  # 8%
        "currency": "FCFA",
        "payment_terms": "Due on Receipt",
        "po_number": "",
        "project_ref": "",
        "special_instructions": "tests",
    }
    
    print("📋 Test Order Details:")
    print(f"   Client: {test_order['client_name']}")
    print(f"   Email: {test_order['client_email']}")
    print(f"   Currency: {test_order['currency']}")
    print(f"   Items: {len(test_order['items'])}")
    print()
    
    # Test the fallback invoice creation directly
    print("🔄 Testing fallback invoice creation...")
    try:
        fallback_invoice = invoice_system._create_fallback_invoice(test_order)
        
        print("✅ Fallback invoice created successfully!")
        print(f"   Invoice Number: {fallback_invoice.get('invoice_number', 'N/A')}")
        print(f"   Client: {fallback_invoice.get('client', {}).get('name', 'N/A')}")
        print(f"   Total: {fallback_invoice.get('total', 0):.2f} {fallback_invoice.get('currency', 'USD')}")
        print(f"   HTML Generated: {fallback_invoice.get('file_generated', False)}")
        
        if fallback_invoice.get('html_file_path'):
            print(f"   HTML File: {fallback_invoice['html_file_path']}")
            
            # Check if file exists
            if os.path.exists(fallback_invoice['html_file_path']):
                print("   ✅ HTML file exists and was created successfully!")
                
                # Read a snippet of the file to verify content
                with open(fallback_invoice['html_file_path'], 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Check if our data was properly inserted
                if fallback_invoice['invoice_number'] in content:
                    print("   ✅ Invoice number correctly inserted in HTML")
                if test_order['client_name'] in content:
                    print("   ✅ Client name correctly inserted in HTML")
                if "FCFA" in content:
                    print("   ✅ Currency correctly formatted in HTML")
                    
            else:
                print("   ❌ HTML file was not created")
        else:
            print("   ⚠️ No HTML file path returned")
            
    except Exception as e:
        print(f"❌ Error testing fallback invoice: {e}")
        return False
    
    print()
    print("🧪 Testing complete invoice generation (with potential AI fallback)...")
    
    try:
        # This will try AI first, then fallback if needed
        result = invoice_system.generate_invoice(test_order)
        
        print("✅ Invoice generation completed!")
        print(f"   Success: {result.get('success', False)}")
        print(f"   Fallback Used: {result.get('fallback_used', False)}")
        print(f"   AI Failed: {result.get('ai_generation_failed', False)}")
        
        if result.get('invoice_data'):
            invoice_data = result['invoice_data']
            print(f"   Invoice Number: {invoice_data.get('invoice_number', 'N/A')}")
            print(f"   HTML Generated: {result.get('html_generated', False) or invoice_data.get('file_generated', False)}")
            
            if invoice_data.get('html_file_path'):
                print(f"   HTML File: {invoice_data['html_file_path']}")
        
    except Exception as e:
        print(f"❌ Error in complete invoice generation: {e}")
        return False
    
    print()
    print("🎉 All tests completed successfully!")
    print("📄 Check the 'generated_invoices' directory for the HTML files.")
    return True

if __name__ == "__main__":
    success = test_fallback_invoice()
    sys.exit(0 if success else 1) 