#!/usr/bin/env python3
"""
Invoice Gallery Component
========================

Displays generated invoices in a gallery format with preview and navigation.
"""

import os
import streamlit as st
from datetime import datetime
from typing import List, Dict, Optional
import re
from pathlib import Path


class InvoiceGalleryComponent:
    """Component for viewing generated invoices in a gallery format."""

    def __init__(self, invoices_folder: str = "generated_invoices"):
        """Initialize the invoice gallery component."""
        self.invoices_folder = invoices_folder
        self.invoices_path = Path(invoices_folder)
        
        # Ensure the folder exists
        self.invoices_path.mkdir(exist_ok=True)

    def render_gallery_button(self) -> bool:
        """Render the button to open invoice gallery."""
        return st.button(
            "📁 View Stored Invoices",
            help="Browse and view all generated invoices",
            key="invoice_gallery_button",
            type="secondary"
        )

    def render_invoice_gallery(self):
        """Render the main invoice gallery interface."""
        st.markdown("## 📁 Invoice Gallery")
        st.markdown("Browse and view all your generated invoices")

        # Get all invoice files
        invoice_files = self._get_invoice_files()

        if not invoice_files:
            st.info("📄 No invoices found. Create some invoices first!")
            return

        # Display invoice count and controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.markdown(f"**Found {len(invoice_files)} invoices**")
        
        with col2:
            view_mode = st.selectbox(
                "View Mode",
                ["Gallery", "List"],
                key="invoice_view_mode"
            )
        
        with col3:
            sort_order = st.selectbox(
                "Sort By",
                ["Newest First", "Oldest First", "Name A-Z", "Name Z-A"],
                key="invoice_sort_order"
            )

        # Sort invoices based on selection
        sorted_invoices = self._sort_invoices(invoice_files, sort_order)

        # Display invoices based on view mode
        if view_mode == "Gallery":
            self._render_gallery_view(sorted_invoices)
        else:
            self._render_list_view(sorted_invoices)

    def _get_invoice_files(self) -> List[Dict]:
        """Get all invoice files with metadata."""
        invoice_files = []
        
        try:
            for file_path in self.invoices_path.glob("*.html"):
                if file_path.is_file():
                    # Extract metadata from filename and file
                    metadata = self._extract_invoice_metadata(file_path)
                    invoice_files.append(metadata)
        except Exception as e:
            st.error(f"Error reading invoice files: {e}")
        
        return invoice_files

    def _extract_invoice_metadata(self, file_path: Path) -> Dict:
        """Extract metadata from invoice file."""
        try:
            # Get basic file info
            stat = file_path.stat()
            
            # Extract invoice number from filename
            filename = file_path.stem
            
            # Try to extract date from filename
            date_match = re.search(r'(\d{8})', filename)
            if date_match:
                date_str = date_match.group(1)
                try:
                    file_date = datetime.strptime(date_str, '%Y%m%d')
                except:
                    file_date = datetime.fromtimestamp(stat.st_mtime)
            else:
                file_date = datetime.fromtimestamp(stat.st_mtime)

            # Read HTML content to extract more details
            content_info = self._parse_invoice_content(file_path)

            return {
                'filename': file_path.name,
                'filepath': str(file_path),
                'invoice_number': filename,
                'file_date': file_date,
                'file_size': stat.st_size,
                'modified_time': datetime.fromtimestamp(stat.st_mtime),
                **content_info
            }
        except Exception as e:
            return {
                'filename': file_path.name,
                'filepath': str(file_path),
                'invoice_number': file_path.stem,
                'file_date': datetime.now(),
                'file_size': 0,
                'modified_time': datetime.now(),
                'client_name': 'Unknown',
                'total_amount': 'Unknown',
                'error': str(e)
            }

    def _parse_invoice_content(self, file_path: Path) -> Dict:
        """Parse HTML content to extract invoice details."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract client name
            client_match = re.search(r'<strong>([^<]+)</strong><br>', content)
            client_name = client_match.group(1) if client_match else 'Unknown Client'

            # Extract total amount
            total_match = re.search(r'<strong>TOTAL:</strong>.*?<strong>([^<]+)</strong>', content, re.DOTALL)
            total_amount = total_match.group(1) if total_match else 'Unknown Amount'

            # Extract invoice date
            date_match = re.search(r'<strong>Invoice Date:</strong>\s*([^<]+)<br>', content)
            invoice_date = date_match.group(1).strip() if date_match else 'Unknown Date'

            return {
                'client_name': client_name,
                'total_amount': total_amount,
                'invoice_date': invoice_date
            }
        except Exception as e:
            return {
                'client_name': 'Unknown',
                'total_amount': 'Unknown',
                'invoice_date': 'Unknown',
                'parse_error': str(e)
            }

    def _sort_invoices(self, invoices: List[Dict], sort_order: str) -> List[Dict]:
        """Sort invoices based on the selected order."""
        if sort_order == "Newest First":
            return sorted(invoices, key=lambda x: x['file_date'], reverse=True)
        elif sort_order == "Oldest First":
            return sorted(invoices, key=lambda x: x['file_date'])
        elif sort_order == "Name A-Z":
            return sorted(invoices, key=lambda x: x['invoice_number'])
        elif sort_order == "Name Z-A":
            return sorted(invoices, key=lambda x: x['invoice_number'], reverse=True)
        else:
            return invoices

    def _render_gallery_view(self, invoices: List[Dict]):
        """Render invoices in gallery view."""
        st.markdown("---")
        
        # Create columns for gallery layout
        cols_per_row = 2
        for i in range(0, len(invoices), cols_per_row):
            cols = st.columns(cols_per_row)
            
            for j, col in enumerate(cols):
                if i + j < len(invoices):
                    invoice = invoices[i + j]
                    with col:
                        self._render_invoice_card(invoice)

    def _render_list_view(self, invoices: List[Dict]):
        """Render invoices in list view."""
        st.markdown("---")
        
        for invoice in invoices:
            with st.expander(
                f"📄 {invoice['invoice_number']} - {invoice['client_name']} ({invoice['total_amount']})",
                expanded=False
            ):
                self._render_invoice_details(invoice)

    def _render_invoice_card(self, invoice: Dict):
        """Render a single invoice card."""
        with st.container():
            # Card header
            st.markdown(f"### 📄 {invoice['invoice_number']}")
            
            # Invoice details
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**Client:** {invoice['client_name']}")
                st.markdown(f"**Date:** {invoice['invoice_date']}")
            with col2:
                st.markdown(f"**Amount:** {invoice['total_amount']}")
                st.markdown(f"**Modified:** {invoice['modified_time'].strftime('%m/%d/%Y')}")

            # Action buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("👁️ Preview", key=f"preview_{invoice['filename']}", use_container_width=True):
                    self._show_invoice_preview(invoice)
            
            with col2:
                if st.button("📱 View Full", key=f"view_{invoice['filename']}", use_container_width=True):
                    self._show_full_invoice(invoice)
            
            with col3:
                if st.button("💾 Download", key=f"download_{invoice['filename']}", use_container_width=True):
                    self._download_invoice(invoice)

            st.markdown("---")

    def _render_invoice_details(self, invoice: Dict):
        """Render detailed invoice information."""
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**📄 Invoice Number:** {invoice['invoice_number']}")
            st.markdown(f"**👤 Client:** {invoice['client_name']}")
            st.markdown(f"**💰 Total Amount:** {invoice['total_amount']}")
            st.markdown(f"**📅 Invoice Date:** {invoice['invoice_date']}")
        
        with col2:
            st.markdown(f"**📁 Filename:** {invoice['filename']}")
            st.markdown(f"**📏 File Size:** {self._format_file_size(invoice['file_size'])}")
            st.markdown(f"**🕒 Modified:** {invoice['modified_time'].strftime('%Y-%m-%d %H:%M:%S')}")

        # Action buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("👁️ Preview", key=f"list_preview_{invoice['filename']}", use_container_width=True):
                self._show_invoice_preview(invoice)
        
        with col2:
            if st.button("📱 View Full", key=f"list_view_{invoice['filename']}", use_container_width=True):
                self._show_full_invoice(invoice)
        
        with col3:
            if st.button("💾 Download", key=f"list_download_{invoice['filename']}", use_container_width=True):
                self._download_invoice(invoice)

    def _show_invoice_preview(self, invoice: Dict):
        """Show invoice preview in a modal-like container."""
        st.markdown(f"### 👁️ Preview: {invoice['invoice_number']}")
        
        try:
            with open(invoice['filepath'], 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Extract just the invoice content (remove full HTML structure for preview)
            preview_content = self._extract_preview_content(html_content)
            
            # Display in a container with limited height
            with st.container():
                st.markdown(
                    f"""
                    <div style="
                        max-height: 400px; 
                        overflow-y: auto; 
                        border: 1px solid #ddd; 
                        padding: 10px; 
                        border-radius: 5px;
                        background: white;
                    ">
                        {preview_content}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                
        except Exception as e:
            st.error(f"Error loading preview: {e}")

    def _show_full_invoice(self, invoice: Dict):
        """Show full invoice in an expandable section."""
        st.markdown(f"### 📱 Full Invoice: {invoice['invoice_number']}")
        
        try:
            with open(invoice['filepath'], 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Display full HTML content
            st.components.v1.html(html_content, height=800, scrolling=True)
                
        except Exception as e:
            st.error(f"Error loading invoice: {e}")

    def _download_invoice(self, invoice: Dict):
        """Provide download functionality for invoice."""
        try:
            with open(invoice['filepath'], 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            st.download_button(
                label=f"📥 Download {invoice['filename']}",
                data=html_content,
                file_name=invoice['filename'],
                mime="text/html",
                key=f"download_btn_{invoice['filename']}"
            )
            
        except Exception as e:
            st.error(f"Error preparing download: {e}")

    def _extract_preview_content(self, html_content: str) -> str:
        """Extract the main content for preview (remove head, scripts, etc.)."""
        try:
            # Extract content between body tags
            body_match = re.search(r'<body[^>]*>(.*?)</body>', html_content, re.DOTALL)
            if body_match:
                return body_match.group(1)
            else:
                # If no body tags, return the content as is
                return html_content
        except:
            return html_content

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"

    def activate_gallery_mode(self):
        """Activate gallery mode in session state."""
        st.session_state.show_invoice_gallery = True

    def deactivate_gallery_mode(self):
        """Deactivate gallery mode in session state."""
        st.session_state.show_invoice_gallery = False 