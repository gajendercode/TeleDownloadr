import asyncio
import questionary

async def test_questionary():
    """Test what questionary actually supports."""

    print("Testing questionary features...")
    print("=" * 60)

    # Create sample data
    choices = [
        "Saved Messages (1087968824)",
        "Tech News Channel (1234567890)",
        "Family Group (-1001234567)",
        "Work Projects (-1009876543)",
        "Finance Updates (-1001111111)",
        "Sports Team (9876543210)",
    ]

    print("\nTest 1: checkbox with use_shortcuts=False")
    print("Try typing to see if it filters...")
    print("-" * 60)

    try:
        result = await questionary.checkbox(
            "Select items (try typing):",
            choices=choices,
            use_shortcuts=False
        ).ask_async()

        print(f"Selected: {result}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n" + "=" * 60)
    print("\nTest 2: autocomplete (supports search)")
    print("Type to filter the list...")
    print("-" * 60)

    try:
        result = await questionary.autocomplete(
            "Search for an item:",
            choices=choices
        ).ask_async()

        print(f"Selected: {result}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_questionary())
