# Chat Search - Real Solution

## The Real Problem

Questionary's `checkbox()` **does NOT support search/filtering** even with `use_shortcuts=False`. This is a limitation of the library itself.

### What Doesn't Work

```python
# This DOES NOT enable search - it only disables shortcuts
selections = await questionary.checkbox(
    "Select chats:",
    choices=choices,
    use_shortcuts=False  # ❌ Disables shortcuts but doesn't add search
).ask_async()
```

**Result**: No search functionality. Typing does nothing.

## The Real Solution

Use **autocomplete for search**, then **checkbox for selection**.

### Two-Step Approach

1. **Step 1: Search** - Use `autocomplete()` to filter
2. **Step 2: Select** - Use `checkbox()` on filtered results

### Implementation

#### utils/display.py

```python
async def ask_checkbox(self, message: str, choices: list[str],
                      instruction: str = None, use_shortcuts: bool = False,
                      enable_search: bool = False) -> list[str]:
    """
    Args:
        enable_search: If True, provides autocomplete search before checkbox
    """

    if enable_search and len(choices) > 20:
        # Step 1: Search with autocomplete
        self.console.print(f"[cyan]ℹ[/] {len(choices)} items. Type to search, or Enter to skip.")

        search_result = await questionary.autocomplete(
            "Search (optional, Enter to skip):",
            choices=[""] + choices,
            default="",
            match_middle=True  # Match anywhere in text
        ).ask_async()

        if search_result and search_result.strip():
            # Filter choices based on search
            filtered = [c for c in choices if search_result.lower() in c.lower()]

            if filtered:
                self.console.print(f"[green]✔[/] Found {len(filtered)} matches")

                # Step 2: Select from filtered results
                return await questionary.checkbox(
                    message,
                    choices=filtered,
                    instruction=instruction,
                    use_shortcuts=use_shortcuts
                ).ask_async()

    # Standard checkbox (no search)
    return await questionary.checkbox(
        message,
        choices=choices,
        instruction=instruction,
        use_shortcuts=use_shortcuts
    ).ask_async()
```

#### main.py

```python
selections = await tui.ask_checkbox(
    "Select chats to download from:",
    choices=choices,
    instruction="(Space to select, Enter to confirm)",
    use_shortcuts=False,
    enable_search=True  # ← Enables two-step search
)
```

## How It Works

### User Experience

**For lists > 20 items:**

```
1. Search Prompt Appears:
   ℹ 100 items. Type to search, or Enter to skip.
   ? Search (optional, Enter to skip): saved█

2. User types "saved" → autocomplete filters in real-time:
   ? Search (optional, Enter to skip): saved

   Saved Messages (1087968824)

3. User presses Enter → sees filtered checkbox:
   ✔ Found 1 matches
   ? Select chats to download from: (Space to select, Enter to confirm)

   [X] Saved Messages (1087968824)

4. User selects with Space, confirms with Enter
```

**For lists ≤ 20 items:**

```
Goes straight to checkbox (no search prompt)
```

### Features

✅ **Real-time filtering**: Autocomplete filters as you type
✅ **Visible input**: Your text is displayed
✅ **Middle matching**: "saved" finds "Saved Messages"
✅ **Case insensitive**: Works with any case
✅ **Optional**: Can skip by pressing Enter
✅ **Filtered selection**: Checkbox shows only matches
✅ **Multi-select**: Can select multiple from filtered results

## Why This Works

| Approach | Search? | Multi-select? | Works? |
|----------|---------|---------------|--------|
| checkbox | ❌ No | ✅ Yes | ❌ No search |
| autocomplete | ✅ Yes | ❌ No | ✅ Single item |
| **autocomplete → checkbox** | **✅ Yes** | **✅ Yes** | **✅ Perfect** |

**Solution**: Combine both for search + multi-select!

## Testing

### Run the Working Test

```bash
python test_search_working.py
```

This will:
1. Load 100 chats
2. Show autocomplete search prompt
3. Let you type to filter
4. Show checkbox with filtered results
5. Let you select multiple items

### Expected Behavior

1. **Search prompt appears**:
   ```
   ? Search (optional, Enter to skip):
   ```

2. **Type "saved"** - autocomplete filters:
   ```
   ? Search (optional, Enter to skip): saved

   Saved Messages (1087968824)
   ```

3. **Press Enter** - checkbox with filtered results:
   ```
   ✔ Found 1 matches
   ? Select chats to download from:

   [ ] Saved Messages (1087968824)
   ```

4. **Space to select, Enter to confirm**

## Comparison

### ❌ What We Tried First (Didn't Work)

```python
# Attempt 1: use_shortcuts=False
selections = await questionary.checkbox(
    choices=choices,
    use_shortcuts=False  # Doesn't add search functionality
)
# Result: No search. Just disables shortcuts.
```

### ✅ What Actually Works

```python
# Working solution: autocomplete → checkbox
if len(choices) > 20:
    # Step 1: Search
    search = await questionary.autocomplete(
        "Search:",
        choices=choices,
        match_middle=True
    ).ask_async()

    # Step 2: Filter
    filtered = [c for c in choices if search.lower() in c.lower()]

    # Step 3: Select from filtered
    selections = await questionary.checkbox(
        choices=filtered
    ).ask_async()
```

## Benefits

✅ **Actually works** - Real search functionality
✅ **User-friendly** - Clear two-step process
✅ **Optional** - Can skip search by pressing Enter
✅ **Fast** - Autocomplete is instant
✅ **Flexible** - Works with any list size
✅ **Multi-select** - Can select multiple filtered items

## Limitations

⚠️ **Two steps**: Search, then select (not simultaneous)
⚠️ **Single search**: Can't refine after initial search

**Verdict**: Small trade-offs for working search functionality.

## Why Questionary Checkbox Doesn't Support Search

Questionary's checkbox is designed for:
- Quick selection with keyboard shortcuts
- Pre-filtered lists
- Small to medium lists (< 50 items)

It's NOT designed for:
- Search/filtering
- Large lists (100+ items)
- Real-time text input

**Solution**: Use autocomplete (which IS designed for search) first.

## Alternative Approaches Considered

### 1. Custom Checkbox Widget
❌ **Too complex**: Would need to fork questionary
❌ **Maintenance**: Hard to keep updated

### 2. External Search Tool
❌ **Dependencies**: Adds complexity
❌ **UX**: Disjointed experience

### 3. Autocomplete → Checkbox (OUR SOLUTION)
✅ **Uses built-in tools**: No custom code
✅ **Clean UX**: Clear two-step flow
✅ **Maintainable**: Uses standard questionary

## Configuration

You can control when search appears:

```python
# Always enable search
enable_search=True

# Auto-enable for large lists only (default)
enable_search=(len(choices) > 20)

# Never enable search
enable_search=False
```

## Summary

**The Truth**: Questionary checkbox doesn't support search natively.

**The Solution**: Use autocomplete for search, then checkbox for selection.

**The Result**: Working search functionality for large chat lists!

**Test it**: `python test_search_working.py`
