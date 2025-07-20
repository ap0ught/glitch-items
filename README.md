# Glitch Items Repository

[![License: CC0-1.0](https://img.shields.io/badge/License-CC0_1.0-lightgrey.svg)](http://creativecommons.org/publicdomain/zero/1.0/)
[![Assets](https://img.shields.io/badge/Assets-5400+-blue.svg)](#)
[![Flash Files](https://img.shields.io/badge/Flash-FLA%20%26%20SWF-red.svg)](#)

A comprehensive collection of game assets from **Glitch**, the beloved browser-based MMO that existed from 2011-2012. This repository contains over 5,400 digital assets including food items, tools, furniture, creatures, and more from the whimsical world of Ur.

## 🎮 About Glitch

Glitch was a unique browser-based massively multiplayer online game created by Tiny Speck. Set in the imagination of 11 giants, players could explore a colorful world, cook elaborate meals, learn skills, chat with NPCs, and collaborate with other players in a non-violent, creativity-focused environment. Though the game shut down in 2012, its assets live on through this open-source repository.

## 📁 Repository Structure

This repository is organized into **26 main categories**, each containing hundreds of individual items:

### 🍎 Core Categories

| Category | Count | Description | Examples |
|----------|-------|-------------|----------|
| **[food/](food/)** | ~195 items | Edible items and ingredients | `apple`, `awesome_stew`, `butterfly_butter` |
| **[tools/](tools/)** | ~25 items | Equipment and machinery | `hoe`, `pick`, `metalmaker`, `woodworker` |
| **[furniture/](furniture/)** | ~72 items | Decorative and functional furniture | Tables, chairs, lamps, storage |
| **[inhabitants/](inhabitants/)** | ~56 items | NPCs and creatures | Animals, characters, pets |
| **[misc/](misc/)** | ~209 items | Various utility items | Books, bags, decorations |

### 🏆 Special Categories

| Category | Description | Examples |
|----------|-------------|----------|
| **[achievements/](achievements/)** | Game achievement badges | Skill mastery, special accomplishments |
| **[artifacts/](artifacts/)** | Rare collectible items | `artifact_butterfly_hair_clip`, `artifact_platinumium_spork` |
| **[alchemy/](alchemy/)** | Crafting components | Potions, compounds, reagents |
| **[cubimals/](cubimals/)** | Collectible cubic animals | Various geometric pets |
| **[giants/](giants/)** | The 11 world-building giants | Pot, Grendaline, Spriggan, etc. |
| **[harvestable_resources/](harvestable_resources/)** | Mineable/gatherable materials | Rocks, trees, plants |
| **[musicblocks/](musicblocks/)** | Musical instruments | Various playable music blocks |
| **[quest_items/](quest_items/)** | Mission-specific items | Special objects for quests |
| **[rare_items/](rare_items/)** | Ultra-rare collectibles | Limited edition items |
| **[seeds/](seeds/)** | Plantable crops | Various seeds for growing |
| **[shrines/](shrines/)** | Religious/spiritual items | Giant shrines and offerings |
| **[trophies/](trophies/)** | Achievement rewards | Race trophies, competition prizes |

## 📊 Asset Statistics

- **Total Files**: 5,395
- **Flash Source Files (.fla)**: 2,610
- **Compiled Flash Files (.swf)**: 2,651
- **Categories**: 26
- **Individual Items**: 1,000+

## 💾 File Types

Each game asset typically includes two files:

- **`.fla`** - Adobe Flash source files (editable)
- **`.swf`** - Compiled Flash files (playable)

## 🚀 Quick Start

### Basic Usage

```bash
# Clone the repository
git clone https://github.com/ap0ught/glitch-items.git
cd glitch-items

# Browse categories
ls -la

# Find specific items
find . -name "*apple*" -type d
find . -name "*tool*" -type d
```

### Working with Assets

```javascript
// Example: Loading SWF in ActionScript/Flash
var loader:Loader = new Loader();
loader.load(new URLRequest("food/apple/apple.swf"));

// Example: File path patterns
// food/[item_name]/[item_name].swf
// tools/[tool_name]/[tool_name].swf
```

### Asset Extraction

```bash
# Extract all SWF files to a directory
find . -name "*.swf" -exec cp {} ./extracted_swfs/ \;

# Get a list of all items by category
for dir in */; do
  echo "=== $dir ==="
  ls "$dir" | head -10
  echo ""
done
```

## 🔍 Finding Items

### Search Examples

```bash
# Find all food items
ls food/

# Find items containing "cheese"
find . -name "*cheese*"

# Find all giant-related items
ls giants/

# Search for tools
ls tools/

# Find magical/rare items
ls rare_items/
ls artifacts/
```

### Popular Items

Some beloved items from the game:

- **Food**: `awesome_stew`, `butterfly_butter`, `chillybusting_chili`
- **Tools**: `high_class_hoe`, `pick`, `watering_can`
- **Creatures**: Various cubimals and inhabitants
- **Artifacts**: `artifact_platinumium_spork`, `artifact_magical_pendant`

## 🛠️ Development

For technical details about working with these assets, see **[README-dev.md](README-dev.md)**.

## 📜 License

All files are provided by Tiny Speck under the [Creative Commons CC0 1.0 Universal License](http://creativecommons.org/publicdomain/zero/1.0/legalcode). This is a broadly permissive "No Rights Reserved" license — you may do what you please with what we've provided.

### Important Notes

- All files are provided **AS-IS**
- Tiny Speck cannot provide support for integrating these assets
- The **Glitch logo and trademark** are *not* included in this license
- No obligation to credit, but links to [glitchthegame.com](http://glitchthegame.com) are appreciated

## 🤝 Contributing

Documentation contributions are welcome! If you figure something out that others could learn from:

1. Write up a quick how-to document
2. Submit it as a pull request
3. Share your knowledge with the community!

### Contribution Ideas

- Asset conversion guides
- Usage examples in different engines
- Categorization improvements
- Tool creation for asset management

## 🔗 Links

- **Game Archive**: [glitchthegame.com](http://glitchthegame.com)
- **Tiny Speck**: [tinyspeck.com](http://tinyspeck.com)
- **Slack**: [slack.com](http://slack.com)

## 🏷️ Tags

`game-assets` `flash` `mmo` `open-source` `creative-commons` `glitch` `tiny-speck` `swf` `fla` `sprites` `animations`
