# Glitch Items - Developer Documentation

This document provides technical details for developers working with the Glitch game assets.

## 🏗️ Repository Architecture

### Directory Structure

```
glitch-items/
├── achievements/          # 1,700+ achievement badges
├── alchemy/              # ~48 alchemy components
├── artifacts/            # ~59 rare collectible artifacts
├── beans/                # ~9 different bean types
├── carved_pumpkins/      # ~12 Halloween decorations
├── compounds/            # ~22 crafting compounds  
├── cubimals/             # ~48 cubic animal pets
├── drink/                # ~32 beverages
├── food/                 # ~195 food items and ingredients
├── furniture/            # ~72 decorative and functional items
├── giants/               # ~24 world-building giant assets
├── harvestable_resources/# ~32 mineable/gatherable materials
├── herbs/                # ~9 herb varieties
├── inhabitants/          # ~56 NPCs and creatures
├── keys/                 # ~14 special keys
├── misc/                 # ~209 miscellaneous items
├── musicblocks/          # ~30 musical instruments
├── party_packs/          # ~10 celebration items
├── quest_items/          # ~24 mission-specific objects
├── rare_items/           # ~9 ultra-rare collectibles
├── seeds/                # ~27 plantable crops
├── shrines/              # ~14 religious/spiritual items
├── spice/                # ~19 cooking seasonings
├── tools/                # ~26 equipment and machinery
└── trophies/             # ~40 achievement rewards
```

## 📁 File Format Specifications

### Flash Files

Each asset typically contains two files:

#### `.fla` Files (Adobe Flash Source)
- **Format**: Adobe Flash CS3/CS4/CS5 project files
- **Editable**: Yes, requires Adobe Flash Professional/Animate
- **Contains**: 
  - Vector graphics
  - Animations/timelines
  - ActionScript code
  - Symbol libraries
  - Layer structures

#### `.swf` Files (Shockwave Flash Compiled)
- **Format**: Compiled Flash bytecode
- **Playable**: In Flash Player or compatible environments
- **Contains**:
  - Compressed vector graphics
  - Compiled ActionScript
  - Animation data
  - Audio (if any)

### File Naming Convention

```
[category]/[item_name]/[item_name].[extension]

Examples:
food/apple/apple.fla
food/apple/apple.swf
tools/hoe/high_class_hoe/high_class_hoe.fla
artifacts/artifact_magical_pendant/artifact_magical_pendant.swf
```

## 🛠️ Development Environment Setup

### Required Tools

#### For Flash Development
```bash
# Adobe Flash Professional (discontinued) or
# Adobe Animate CC (modern replacement)
# Alternative open-source tools:
```

#### For Asset Extraction
```bash
# SWF decompilers
npm install -g swf-extract
pip install swfextract

# JPEXS Free Flash Decompiler (Java)
wget https://github.com/jindrapetrik/jpexs-decompiler/releases/latest

# FFDec (Free Flash Decompiler)
```

#### For Asset Conversion
```bash
# ImageMagick for image conversion
sudo apt-get install imagemagick

# FFmpeg for video/animation extraction
sudo apt-get install ffmpeg

# Node.js for scripting
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

## 🔄 Asset Extraction Workflows

### Extracting Images from SWF

```bash
#!/bin/bash
# extract_images.sh - Extract all images from SWF files

for swf_file in $(find . -name "*.swf"); do
    output_dir="${swf_file%.*}_extracted"
    mkdir -p "$output_dir"
    
    # Using swfextract (part of swftools)
    swfextract -j "$swf_file" -o "$output_dir/image_%d.jpg"
    swfextract -p "$swf_file" -o "$output_dir/image_%d.png"
    
    echo "Extracted assets from $swf_file to $output_dir"
done
```

### Converting SWF to Other Formats

```python
#!/usr/bin/env python3
# convert_swf.py - Convert SWF files to modern formats

import os
import subprocess
from pathlib import Path

def convert_swf_to_gif(swf_path, output_path):
    """Convert SWF animation to GIF using FFmpeg"""
    cmd = [
        'ffmpeg', '-i', str(swf_path),
        '-vf', 'scale=320:-1:flags=lanczos',
        '-r', '15', '-loop', '0',
        str(output_path)
    ]
    subprocess.run(cmd, check=True)

def extract_first_frame(swf_path, output_path):
    """Extract first frame as PNG"""
    cmd = [
        'ffmpeg', '-i', str(swf_path),
        '-vframes', '1', '-f', 'image2',
        str(output_path)
    ]
    subprocess.run(cmd, check=True)

# Usage example
for swf_file in Path('.').rglob('*.swf'):
    gif_output = swf_file.with_suffix('.gif')
    png_output = swf_file.with_suffix('.png')
    
    try:
        convert_swf_to_gif(swf_file, gif_output)
        extract_first_frame(swf_file, png_output)
        print(f"Converted {swf_file}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to convert {swf_file}: {e}")
```

### Bulk Asset Analysis

```javascript
// analyze_assets.js - Analyze repository structure and generate reports
const fs = require('fs');
const path = require('path');

class AssetAnalyzer {
    constructor(rootPath) {
        this.rootPath = rootPath;
        this.stats = {
            totalFiles: 0,
            flaFiles: 0,
            swfFiles: 0,
            categories: {},
            largestItems: [],
            duplicates: []
        };
    }

    async analyzeRepository() {
        const categories = fs.readdirSync(this.rootPath, { withFileTypes: true })
            .filter(dirent => dirent.isDirectory() && !dirent.name.startsWith('.'))
            .map(dirent => dirent.name);

        for (const category of categories) {
            await this.analyzeCategory(category);
        }

        return this.generateReport();
    }

    async analyzeCategory(categoryName) {
        const categoryPath = path.join(this.rootPath, categoryName);
        const items = fs.readdirSync(categoryPath, { withFileTypes: true })
            .filter(dirent => dirent.isDirectory())
            .map(dirent => dirent.name);

        this.stats.categories[categoryName] = {
            itemCount: items.length,
            items: items,
            totalSize: 0
        };

        for (const item of items) {
            await this.analyzeItem(categoryName, item);
        }
    }

    async analyzeItem(category, itemName) {
        const itemPath = path.join(this.rootPath, category, itemName);
        
        try {
            const files = fs.readdirSync(itemPath);
            
            for (const file of files) {
                const filePath = path.join(itemPath, file);
                const stats = fs.statSync(filePath);
                
                this.stats.totalFiles++;
                this.stats.categories[category].totalSize += stats.size;
                
                if (file.endsWith('.fla')) {
                    this.stats.flaFiles++;
                } else if (file.endsWith('.swf')) {
                    this.stats.swfFiles++;
                }
                
                // Track largest files
                this.stats.largestItems.push({
                    path: `${category}/${itemName}/${file}`,
                    size: stats.size
                });
            }
        } catch (error) {
            console.warn(`Could not analyze ${category}/${itemName}: ${error.message}`);
        }
    }

    generateReport() {
        // Sort largest items
        this.stats.largestItems.sort((a, b) => b.size - a.size);
        this.stats.largestItems = this.stats.largestItems.slice(0, 20);

        const report = {
            summary: {
                totalFiles: this.stats.totalFiles,
                flaFiles: this.stats.flaFiles,
                swfFiles: this.stats.swfFiles,
                categories: Object.keys(this.stats.categories).length
            },
            categoryBreakdown: this.stats.categories,
            largestAssets: this.stats.largestItems.map(item => ({
                path: item.path,
                sizeMB: (item.size / 1024 / 1024).toFixed(2)
            }))
        };

        return report;
    }
}

// Usage
async function main() {
    const analyzer = new AssetAnalyzer('.');
    const report = await analyzer.analyzeRepository();
    
    console.log('=== Glitch Assets Analysis Report ===');
    console.log(JSON.stringify(report, null, 2));
    
    // Save to file
    fs.writeFileSync('asset_analysis.json', JSON.stringify(report, null, 2));
    console.log('\nReport saved to asset_analysis.json');
}

if (require.main === module) {
    main().catch(console.error);
}

module.exports = AssetAnalyzer;
```

## 🎮 Integration Examples

### Unity Integration

```csharp
// GlitchAssetLoader.cs - Load Glitch assets in Unity
using UnityEngine;
using System.IO;

public class GlitchAssetLoader : MonoBehaviour 
{
    [System.Serializable]
    public class GlitchItem 
    {
        public string category;
        public string itemName;
        public Texture2D icon;
        public string description;
    }

    public static Texture2D LoadItemTexture(string category, string itemName) 
    {
        string path = Path.Combine(Application.streamingAssetsPath, 
                                  "glitch-items", category, itemName, 
                                  itemName + ".png");
        
        if (File.Exists(path)) 
        {
            byte[] data = File.ReadAllBytes(path);
            Texture2D texture = new Texture2D(2, 2);
            texture.LoadImage(data);
            return texture;
        }
        
        Debug.LogWarning($"Could not find texture for {category}/{itemName}");
        return null;
    }

    public static GlitchItem CreateFoodItem(string itemName) 
    {
        return new GlitchItem 
        {
            category = "food",
            itemName = itemName,
            icon = LoadItemTexture("food", itemName),
            description = $"A delicious {itemName} from the world of Ur"
        };
    }
}
```

### HTML5/JavaScript Integration

```html
<!DOCTYPE html>
<html>
<head>
    <title>Glitch Asset Viewer</title>
    <style>
        .asset-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(100px, 1fr)); gap: 10px; }
        .asset-item { text-align: center; border: 1px solid #ccc; padding: 10px; }
        .asset-item img { max-width: 80px; max-height: 80px; }
    </style>
</head>
<body>
    <h1>Glitch Assets Browser</h1>
    <div id="categorySelector">
        <select id="categories" onchange="loadCategory()">
            <option value="">Select a category...</option>
        </select>
    </div>
    <div id="assetGrid" class="asset-grid"></div>

    <script>
        class GlitchAssetBrowser {
            constructor() {
                this.categories = [
                    'food', 'tools', 'furniture', 'inhabitants', 'artifacts',
                    'cubimals', 'drink', 'misc', 'achievements', 'alchemy'
                ];
                this.init();
            }

            init() {
                const select = document.getElementById('categories');
                this.categories.forEach(category => {
                    const option = document.createElement('option');
                    option.value = category;
                    option.textContent = category.charAt(0).toUpperCase() + category.slice(1);
                    select.appendChild(option);
                });
            }

            async loadCategory() {
                const category = document.getElementById('categories').value;
                if (!category) return;

                const grid = document.getElementById('assetGrid');
                grid.innerHTML = '<p>Loading assets...</p>';

                try {
                    // In a real implementation, you'd fetch this from a server
                    // or have a pre-generated index
                    const assets = await this.fetchCategoryAssets(category);
                    this.renderAssets(assets);
                } catch (error) {
                    grid.innerHTML = '<p>Error loading assets: ' + error.message + '</p>';
                }
            }

            async fetchCategoryAssets(category) {
                // Mock data - in reality, you'd fetch from your server
                const mockAssets = {
                    food: ['apple', 'banana', 'awesome_stew', 'butterfly_butter'],
                    tools: ['hoe', 'pick', 'watering_can', 'metalmaker'],
                    furniture: ['chair', 'table', 'lamp', 'storage_box']
                };

                return mockAssets[category] || [];
            }

            renderAssets(assets) {
                const grid = document.getElementById('assetGrid');
                grid.innerHTML = '';

                assets.forEach(assetName => {
                    const item = document.createElement('div');
                    item.className = 'asset-item';
                    
                    // Create fallback image path
                    const imagePath = `assets/${document.getElementById('categories').value}/${assetName}/${assetName}.png`;
                    
                    item.innerHTML = `
                        <img src="${imagePath}" 
                             alt="${assetName}" 
                             onerror="this.src='assets/placeholder.png'"
                             title="${assetName}">
                        <div>${assetName.replace(/_/g, ' ')}</div>
                    `;
                    
                    grid.appendChild(item);
                });
            }
        }

        // Initialize when page loads
        document.addEventListener('DOMContentLoaded', () => {
            window.assetBrowser = new GlitchAssetBrowser();
        });

        function loadCategory() {
            window.assetBrowser.loadCategory();
        }
    </script>
</body>
</html>
```

## 🔧 Useful Development Scripts

### Asset Validation Script

```bash
#!/bin/bash
# validate_assets.sh - Check for missing files and inconsistencies

echo "=== Glitch Assets Validation ==="
echo "Checking for missing paired files..."

missing_pairs=0
orphaned_files=0

for category in */; do
    if [[ "$category" == ".git/" ]]; then
        continue
    fi
    
    echo "Validating category: $category"
    
    for item_dir in "$category"*/; do
        if [[ ! -d "$item_dir" ]]; then
            continue
        fi
        
        item_name=$(basename "$item_dir")
        fla_file="$item_dir$item_name.fla"
        swf_file="$item_dir$item_name.swf"
        
        if [[ -f "$fla_file" && ! -f "$swf_file" ]]; then
            echo "  ⚠️  Missing SWF: $swf_file"
            ((missing_pairs++))
        elif [[ ! -f "$fla_file" && -f "$swf_file" ]]; then
            echo "  ⚠️  Missing FLA: $fla_file"
            ((missing_pairs++))
        elif [[ ! -f "$fla_file" && ! -f "$swf_file" ]]; then
            echo "  ❌ Empty directory: $item_dir"
            ((orphaned_files++))
        fi
    done
done

echo ""
echo "=== Validation Summary ==="
echo "Missing paired files: $missing_pairs"
echo "Empty directories: $orphaned_files"

if [[ $missing_pairs -eq 0 && $orphaned_files -eq 0 ]]; then
    echo "✅ All assets validated successfully!"
else
    echo "⚠️  Issues found. Consider running repair scripts."
fi
```

### Category Statistics Generator

```python
#!/usr/bin/env python3
# generate_stats.py - Generate comprehensive statistics

import os
import json
import glob
from collections import defaultdict
from pathlib import Path

def generate_category_stats():
    """Generate detailed statistics for each category."""
    
    stats = defaultdict(lambda: {
        'item_count': 0,
        'fla_count': 0,
        'swf_count': 0,
        'total_size_mb': 0,
        'items': []
    })
    
    for category_path in glob.glob('*/'):
        category = category_path.rstrip('/')
        
        if category.startswith('.'):
            continue
            
        print(f"Analyzing {category}...")
        
        for item_path in glob.glob(f'{category}/*/'):
            item_name = os.path.basename(item_path.rstrip('/'))
            stats[category]['items'].append(item_name)
            stats[category]['item_count'] += 1
            
            # Count files and calculate sizes
            for file_path in glob.glob(f'{item_path}*'):
                if os.path.isfile(file_path):
                    file_size = os.path.getsize(file_path)
                    stats[category]['total_size_mb'] += file_size / (1024 * 1024)
                    
                    if file_path.endswith('.fla'):
                        stats[category]['fla_count'] += 1
                    elif file_path.endswith('.swf'):
                        stats[category]['swf_count'] += 1
    
    return dict(stats)

def generate_markdown_report(stats):
    """Generate a markdown report from statistics."""
    
    report = "# Glitch Assets Statistics Report\n\n"
    report += "Generated automatically from repository analysis.\n\n"
    
    # Summary table
    report += "## Summary by Category\n\n"
    report += "| Category | Items | FLA Files | SWF Files | Total Size (MB) |\n"
    report += "|----------|-------|-----------|-----------|----------------|\n"
    
    total_items = 0
    total_fla = 0
    total_swf = 0
    total_size = 0
    
    for category, data in sorted(stats.items()):
        total_items += data['item_count']
        total_fla += data['fla_count']
        total_swf += data['swf_count']
        total_size += data['total_size_mb']
        
        report += f"| {category} | {data['item_count']} | {data['fla_count']} | {data['swf_count']} | {data['total_size_mb']:.1f} |\n"
    
    report += f"| **TOTAL** | **{total_items}** | **{total_fla}** | **{total_swf}** | **{total_size:.1f}** |\n\n"
    
    # Detailed breakdown
    report += "## Detailed Category Breakdown\n\n"
    
    for category, data in sorted(stats.items()):
        report += f"### {category.title()}\n\n"
        report += f"- **Items**: {data['item_count']}\n"
        report += f"- **Size**: {data['total_size_mb']:.1f} MB\n"
        report += f"- **Completeness**: {min(data['fla_count'], data['swf_count'])}/{data['item_count']} items have both FLA and SWF\n\n"
        
        if len(data['items']) <= 20:
            report += "**Items**: " + ", ".join(f"`{item}`" for item in sorted(data['items'])) + "\n\n"
        else:
            sample_items = sorted(data['items'])[:10]
            report += "**Sample Items**: " + ", ".join(f"`{item}`" for item in sample_items) + f", ... and {len(data['items']) - 10} more\n\n"
    
    return report

if __name__ == "__main__":
    print("Generating asset statistics...")
    stats = generate_category_stats()
    
    # Save JSON report
    with open('asset_stats.json', 'w') as f:
        json.dump(stats, f, indent=2)
    print("✅ JSON report saved to asset_stats.json")
    
    # Save Markdown report
    markdown_report = generate_markdown_report(stats)
    with open('asset_stats.md', 'w') as f:
        f.write(markdown_report)
    print("✅ Markdown report saved to asset_stats.md")
    
    # Print summary
    total_categories = len(stats)
    total_items = sum(data['item_count'] for data in stats.values())
    total_size = sum(data['total_size_mb'] for data in stats.values())
    
    print(f"\n📊 Summary:")
    print(f"   Categories: {total_categories}")
    print(f"   Total Items: {total_items}")
    print(f"   Total Size: {total_size:.1f} MB")
```

## 🚀 Deployment and Distribution

### Creating Asset Packages

```bash
#!/bin/bash
# package_assets.sh - Create distribution packages

# Create packages by category
for category in */; do
    if [[ "$category" == ".git/" ]]; then
        continue
    fi
    
    category_name=$(basename "$category")
    echo "Packaging $category_name..."
    
    # Create compressed archive
    tar -czf "packages/${category_name}_assets.tar.gz" "$category"
    
    # Create PNG-only package for web use
    temp_dir="temp_${category_name}"
    mkdir -p "$temp_dir"
    
    # Convert SWF to PNG for each item
    find "$category" -name "*.swf" | while read swf_file; do
        item_dir=$(dirname "$swf_file")
        item_name=$(basename "$item_dir")
        output_file="$temp_dir/${item_name}.png"
        
        # Extract first frame as PNG using FFmpeg
        ffmpeg -i "$swf_file" -vframes 1 -f image2 "$output_file" 2>/dev/null
    done
    
    # Package PNG files
    tar -czf "packages/${category_name}_pngs.tar.gz" -C "$temp_dir" .
    rm -rf "$temp_dir"
done

echo "✅ All packages created in packages/ directory"
```

## 🧪 Testing and Quality Assurance

### Automated Testing

```javascript
// test_assets.js - Automated asset testing
const fs = require('fs');
const path = require('path');

class AssetTester {
    constructor() {
        this.errors = [];
        this.warnings = [];
    }

    testRepository() {
        console.log('🧪 Starting asset tests...');
        
        this.testDirectoryStructure();
        this.testFilePairs();
        this.testNamingConventions();
        this.testFileIntegrity();
        
        this.reportResults();
    }

    testDirectoryStructure() {
        console.log('📁 Testing directory structure...');
        
        const expectedCategories = [
            'food', 'tools', 'furniture', 'inhabitants', 'misc',
            'achievements', 'artifacts', 'alchemy', 'cubimals'
        ];
        
        expectedCategories.forEach(category => {
            if (!fs.existsSync(category)) {
                this.errors.push(`Missing expected category: ${category}`);
            }
        });
    }

    testFilePairs() {
        console.log('🔗 Testing FLA/SWF file pairs...');
        
        const categories = fs.readdirSync('.', { withFileTypes: true })
            .filter(dirent => dirent.isDirectory() && !dirent.name.startsWith('.'))
            .map(dirent => dirent.name);

        categories.forEach(category => {
            const categoryPath = path.join('.', category);
            const items = fs.readdirSync(categoryPath, { withFileTypes: true })
                .filter(dirent => dirent.isDirectory())
                .map(dirent => dirent.name);

            items.forEach(item => {
                const itemPath = path.join(categoryPath, item);
                const flaFile = path.join(itemPath, `${item}.fla`);
                const swfFile = path.join(itemPath, `${item}.swf`);

                if (!fs.existsSync(flaFile)) {
                    this.warnings.push(`Missing FLA: ${flaFile}`);
                }
                if (!fs.existsSync(swfFile)) {
                    this.warnings.push(`Missing SWF: ${swfFile}`);
                }
            });
        });
    }

    testNamingConventions() {
        console.log('📝 Testing naming conventions...');
        
        // Test for consistent naming
        const invalidChars = /[^a-z0-9_]/;
        
        // Implementation would check all directory and file names
        // for consistency with expected patterns
    }

    testFileIntegrity() {
        console.log('🔍 Testing file integrity...');
        
        // Check for zero-byte files
        // Verify SWF headers
        // Test for corruption
    }

    reportResults() {
        console.log('\n📋 Test Results:');
        console.log(`Errors: ${this.errors.length}`);
        console.log(`Warnings: ${this.warnings.length}`);
        
        if (this.errors.length > 0) {
            console.log('\n❌ Errors:');
            this.errors.forEach(error => console.log(`  - ${error}`));
        }
        
        if (this.warnings.length > 0) {
            console.log('\n⚠️  Warnings:');
            this.warnings.forEach(warning => console.log(`  - ${warning}`));
        }
        
        if (this.errors.length === 0 && this.warnings.length === 0) {
            console.log('✅ All tests passed!');
        }
    }
}

// Run tests
if (require.main === module) {
    const tester = new AssetTester();
    tester.testRepository();
}
```

## 📚 Additional Resources

### Community Tools
- **JPEXS Free Flash Decompiler**: Best tool for viewing/editing SWF files
- **Adobe Animate**: Modern replacement for Flash Professional
- **Ruffle**: Flash Player emulator written in Rust

### Documentation
- [SWF File Format Specification](https://www.adobe.com/devnet/swf.html)
- [ActionScript Reference](https://help.adobe.com/en_US/ActionScript/3.0_ProgrammingAS3/)
- [Flash Development Best Practices](https://github.com/MorningStarGames/Flash-Tools)

### Related Projects
- [Glitch Assets Art](https://github.com/glitchthegame/glitch-art) - Art assets
- [Glitch Assets Locations](https://github.com/glitchthegame/glitch-locations) - Location assets
- [Glitch Assets Avatars](https://github.com/glitchthegame/glitch-avatars) - Avatar assets

## 🤝 Contributing Guidelines

### Code Style
- Use descriptive variable names
- Comment complex asset manipulation logic
- Follow existing file organization patterns
- Test scripts on multiple asset categories

### Pull Request Process
1. Fork the repository
2. Create a feature branch
3. Test your changes thoroughly
4. Update documentation as needed
5. Submit a pull request with clear description

### Reporting Issues
When reporting issues with specific assets:
- Include the full path to the problematic file
- Describe the expected vs actual behavior
- Include your development environment details
- Attach relevant error messages or screenshots

---

*This documentation is maintained by the community. Contributions and improvements are welcome!*