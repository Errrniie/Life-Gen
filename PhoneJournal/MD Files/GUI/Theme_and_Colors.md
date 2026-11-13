# Theme & Colors (JournalErnie)

This document describes where app colors live, how the Material3 theme is wired, and what to use when adding or editing UI.

## Quick reference

| What you need | Where to get it |
|---------------|-----------------|
| App background (plum) | `MaterialTheme.colorScheme.background` |
| Cards / elevated surfaces | `MaterialTheme.colorScheme.surface` |
| Text on plum backgrounds | `MaterialTheme.colorScheme.onBackground` or `onSurface` |
| Primary accent (weight ring, active states) | `MaterialTheme.colorScheme.primary` |
| Delete / destructive | `MaterialTheme.colorScheme.error` |
| Exercise / warmup / cardio block tint | `blockTypeColor(blockType)` |
| Calendar, rest day, picker buttons, etc. | `workoutColors().…` |
| Change a color app-wide | Edit `ui/theme/Color.kt` or `WorkoutColors.kt` only |

**Rule:** Do not add new `Color(0xFF…)` literals in screens or components. Put raw hex values in `ui/theme/` and read them through the theme APIs below.

---

## File layout

All theme code lives under:

```
JournalErnie/app/src/main/java/com/journal/ernie/ui/theme/
├── Color.kt          # Raw palette tokens + Material3 AppColorScheme
├── WorkoutColors.kt  # Workout-specific semantics + blockTypeColor()
└── Theme.kt          # JournalErnieTheme composable (app entry theme)
```

Optional scaffold helper (not required on every screen):

```
JournalErnie/app/src/main/java/com/journal/ernie/ui/components/AppScaffold.kt
```

---

## How the theme is applied

### 1. Root: `MainActivity.kt`

The entire Compose tree is wrapped in `JournalErnieTheme`. The root `Surface` uses the theme background — no hardcoded plum hex here.

```kotlin
JournalErnieTheme {
    Surface(
        modifier = Modifier.fillMaxSize(),
        color = MaterialTheme.colorScheme.background
    ) {
        AppNavigation(...)
    }
}
```

Every screen and component inside `AppNavigation` inherits this theme automatically.

### 2. `JournalErnieTheme` (`Theme.kt`)

`JournalErnieTheme` does two things:

1. Sets **Material3** `colorScheme` to `AppColorScheme` (from `Color.kt`).
2. Provides **workout semantics** via `CompositionLocalProvider(LocalWorkoutColors …)`.

There is no separate light theme — the app is a dark plum UI, so `AppColorScheme` is built with `darkColorScheme(...)`.

### 3. Two color layers

```
┌─────────────────────────────────────────────────────────┐
│  JournalErnieTheme                                      │
│  ┌───────────────────────────────────────────────────┐  │
│  │  MaterialTheme.colorScheme  (standard M3 slots)   │  │
│  │  background, surface, primary, error, onSurface… │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │  LocalWorkoutColors → workoutColors()             │  │
│  │  exercise, warmup, cardio, restDay, monthContainer│  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

- **Material3 slots** — backgrounds, cards, text, primary accent, errors. Use `MaterialTheme.colorScheme.*` in composables.
- **Workout semantics** — block types, calendar tints, picker confirm/cancel, weight-ring extras. Use `workoutColors()` or `blockTypeColor()`.

---

## `Color.kt` — palette & Material3 mapping

Raw tokens (the only place `#3B2345`-style literals should live for app chrome):

| Token | Hex | Mapped to `AppColorScheme` |
|-------|-----|----------------------------|
| `PlumBackground` | `#3B2345` | `background` |
| `PlumSurface` | `#4A2F55` | `surface`, `primaryContainer` |
| `OnPlum` | `#F0E8F2` | `onBackground`, `onSurface`, `onPrimaryContainer` |
| `PrimaryAccent` | `#5C7A9E` | `primary` |
| `Destructive` | `#B85C5C` | `error` |

Weight ring neutrals (not part of M3 scheme; used directly in `WeightRingPicker`):

| Token | Hex |
|-------|-----|
| `RingNeutral1` … `RingNeutral5` | `#8E8E8E`, `#757575`, `#9A9A9A`, `#707070`, `#858585` |
| `RingFineNeutral` | `#AAAAAA` |
| `RingNeutralColors` | List of the five ring neutrals |

**To change the app background or app bar color everywhere:** edit `PlumBackground` in `Color.kt`. All scaffolds and top bars read `MaterialTheme.colorScheme.background`.

**To change card/surface tint:** edit `PlumSurface`.

---

## `WorkoutColors.kt` — workout semantics

`WorkoutColors` holds colors that are not standard Material3 roles:

| Property | Hex | Typical use |
|----------|-----|-------------|
| `exercise` | `#7A7A7A` | Exercise blocks, accents |
| `warmup` | `#4FA3A5` | Warmup blocks |
| `cardio` | `#B8864B` | Cardio blocks (canonical; unified from older mixed values) |
| `restDay` | `#5A9A7A` | Rest-day cards on workout list |
| `missedDay` | `#B85C5C` (same as `Destructive`) | Missed-workout cards |
| `currentWeekAccent` | `#7A7A7A` | Calendar current-week highlight |
| `monthContainer` | `#E6E6E6` @ 75% alpha | Month header container on workout list |
| `confirm` | `#2E7D32` | Picker confirm (e.g. equipment wheel) |
| `confirmDisabled` | `#6B6B6B` | Disabled confirm |
| `cancel` | `#D32F2F` | Picker cancel |
| `weightRingAnchor` | `#B8864B` | Weight ring anchor styling |
| `weightRingFineNeutral` | `#AAAAAA` | Fine-pick overlay neutral |

Access in composables:

```kotlin
val palette = workoutColors()
Card(containerColor = palette.restDay.copy(alpha = 0.12f))
```

For block types, prefer the helper (avoids duplicating `when (blockType)`):

```kotlin
val accentColor = blockTypeColor(block.type)
// EXERCISE → exercise, WARMUP_GROUP → warmup, CARDIO_GROUP → cardio
```

**To change exercise block color everywhere:** edit `exercise` in `defaultWorkoutColors()` in `WorkoutColors.kt`.

---

## What to use in screens & components

### Scaffolds and top app bars

Use the theme background — not a hex literal:

```kotlin
Scaffold(
    containerColor = MaterialTheme.colorScheme.background,
    topBar = {
        TopAppBar(
            colors = TopAppBarDefaults.topAppBarColors(
                containerColor = MaterialTheme.colorScheme.background
            ),
            ...
        )
    }
)
```

Or use `AppScaffold` for simple screens with a title and optional back button; it applies the same colors internally.

Screens with custom top bars (e.g. `JournalScreen` tabs) can keep a raw `Scaffold` but must still use `MaterialTheme.colorScheme.background`.

### Cards

```kotlin
Card(
    colors = CardDefaults.cardColors(
        containerColor = MaterialTheme.colorScheme.surface
    )
)
```

For tinted workout cards (rest/missed day), use `workoutColors()` with alpha — do not invent new hex values.

### Text

On plum backgrounds:

```kotlin
color = MaterialTheme.colorScheme.onBackground
// or
color = MaterialTheme.colorScheme.onSurface
```

`HomeScreen` already uses `primaryContainer` / `onPrimaryContainer` for navigation tiles — keep that pattern for home-specific cards.

### Destructive actions

```kotlin
Icon(tint = MaterialTheme.colorScheme.error)
Text("Delete", color = MaterialTheme.colorScheme.error)
```

### Block cards and session UI

| File | Theme API |
|------|-----------|
| `WorkoutBlockCard.kt` | `blockTypeColor(type)` |
| `WorkoutSessionScreen.kt` | `workoutColors()` |
| `WorkoutListScreen.kt` | `workoutColors()` (calendar, rest/missed cards) |
| `WeightRingPicker.kt` | `PrimaryAccent`, `RingNeutralColors`, `defaultWorkoutColors()` |
| `EquipmentExerciseWheelOverlay.kt` | `workoutColors()` (confirm/cancel) |

---

## Adding a new color

1. **App-wide chrome** (background, surface, primary, error) → add token in `Color.kt`, map it in `AppColorScheme`, use `MaterialTheme.colorScheme.*`.
2. **Workout-only meaning** (new block type, calendar state, picker state) → add field to `WorkoutColors`, set it in `defaultWorkoutColors()`, read via `workoutColors()`.
3. **Block type mapping** → extend `blockTypeColor()` if it should follow `BlockType`.

Do not scatter `Color(0xFF…)` in `ui/`, `ui/components/`, or `ui/dialogs/`.

---

## Exceptions

These are intentional:

- **All raw hex literals** belong in `ui/theme/Color.kt` and `ui/theme/WorkoutColors.kt`.
- **`Color.White`**, **`Color.Transparent`**, and **`.copy(alpha = …)`** on theme colors are fine in UI code.
- **`WeightRingPicker`** imports `PrimaryAccent` and `RingNeutralColors` directly from `Color.kt` (ring gradient list is theme-owned).

After migration, grepping for `Color(0x` outside `ui/theme/` should return no matches.

---

## Changing the look globally (examples)

| Goal | Edit |
|------|------|
| Darker/lighter app background | `PlumBackground` in `Color.kt` |
| Card color on all screens | `PlumSurface` in `Color.kt` |
| Weight ring selected color | `PrimaryAccent` in `Color.kt` (also `colorScheme.primary`) |
| Delete icon red | `Destructive` in `Color.kt` (also `colorScheme.error`) |
| Cardio block orange | `cardio` in `WorkoutColors.kt` |
| Rest day green tint | `restDay` in `WorkoutColors.kt` |

Rebuild/run the app after theme edits; no per-screen changes are needed if UI code already uses the theme APIs.

---

## Related files

- `MainActivity.kt` — applies `JournalErnieTheme`
- `ui/components/AppScaffold.kt` — optional shared scaffold (theme-aware top bar)
- `MD Files/GUI.md` — screen-level UI spec (navigation, layouts)
- `MD Files/Workout_Section_Agent_Handoff.md` — workout feature context for agents
