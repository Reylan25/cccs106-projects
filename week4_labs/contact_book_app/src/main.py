import flet as ft
from database import init_db
from app_logic import display_contacts, add_contact

def main(page: ft.Page):
    page.title = "Contact Book"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.scroll = "auto"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 420
    page.window_height = 700

    db_conn = init_db()

    # ---------------- Logo / Header ----------------
    header = ft.Column(
        [
            ft.Icon(name=ft.Icons.CONTACT_PHONE, size=80, color=ft.Colors.BLUE_600),
            ft.Text("My Contacts", size=28, weight=ft.FontWeight.BOLD, text_align="center"),
            ft.Divider(),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # ---------------- Input Fields ----------------
    name_input = ft.TextField(label="Name", width=350, border_radius=12)
    phone_input = ft.TextField(label="Phone", width=350, border_radius=12)
    email_input = ft.TextField(label="Email", width=350, border_radius=12)
    inputs = (name_input, phone_input, email_input)

    add_button = ft.ElevatedButton(
        text="➕ Add Contact",
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=12),
            padding=20,
            bgcolor=ft.Colors.BLUE_600,
            color=ft.Colors.WHITE,
        ),
        on_click=lambda e: add_contact(page, inputs, contacts_list_view, db_conn),
    )

    input_card = ft.Card(
        content=ft.Container(
            content=ft.Column(
                [
                    ft.Text("Add a New Contact", size=20, weight=ft.FontWeight.W_600),
                    name_input,
                    phone_input,
                    email_input,
                    add_button,
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            padding=20,
        )
    )

    # ---------------- Search Bar ----------------
    search_input = ft.TextField(
        label="🔍 Search Contact",
        width=350,
        border_radius=12,
        on_change=lambda e: display_contacts(page, contacts_list_view, db_conn, e.control.value),
    )

    # ---------------- Dark Mode Switch ----------------
    theme_switch = ft.Switch(
        label="Dark Mode",
        on_change=lambda e: setattr(page, "theme_mode", ft.ThemeMode.DARK if e.control.value else ft.ThemeMode.LIGHT) or page.update(),
    )

    # ---------------- Contacts List ----------------
    contacts_list_view = ft.ListView(expand=1, spacing=10, auto_scroll=True)

    contacts_section = ft.Column(
        [
            ft.Text("Saved Contacts", size=22, weight=ft.FontWeight.BOLD),
            contacts_list_view,
        ],
        spacing=10,
    )

    # ---------------- Layout ----------------
    page.add(
        ft.Column(
            [
                header,
                input_card,
                search_input,
                theme_switch,
                ft.Divider(),
                contacts_section,
            ],
            spacing=20,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            expand=True,
        )
    )

    # Load existing contacts
    display_contacts(page, contacts_list_view, db_conn)

if __name__ == "__main__":
    ft.app(target=main)
