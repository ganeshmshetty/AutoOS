# Task Mining Chrome Extension

A Chrome extension that captures user workflows and interactions for task mining analysis, featuring advanced noise reduction and data export capabilities.

## 📁 Project Structure

```
extension/
├── manifest.json                    # Extension configuration
├── src/
│   ├── background/
│   │   └── background.js           # Service worker for IndexedDB operations
│   ├── content/
│   │   └── content.js              # Content script with event capture
│   ├── ui/
│   │   ├── popup.html              # Extension popup interface
│   │   ├── popup.js                # Popup logic
│   │   ├── dashboard.html          # Main dashboard interface
│   │   └── dashboard.js            # Dashboard logic with analytics
│   └── utils/
│       ├── noiseReduction.js       # Noise filtering module
│       └── csvExporter.js          # CSV export functionality
└── public/                          # Static assets
```

## 🚀 Features

### 1. **Comprehensive Event Capture**
- Clicks, inputs, navigation, scrolls
- Form submissions and interactions
- Focus/blur events
- Drag and drop operations
- SPA navigation tracking
- DOM mutation detection
- Page visibility changes

### 2. **Noise Reduction (Section 2.6 Implementation)**
The extension implements intelligent noise reduction to filter unnecessary data:

- **Event Combining**: Merges consecutive similar events (scroll, mouse moves, rapid typing)
- **Threshold Filtering**: Ignores minor scroll movements (< 50px) and mouse movements (< 20px)
- **Insignificant Element Filtering**: Excludes events on SCRIPT, STYLE, LINK, META tags
- **Visibility-based Filtering**: Skips heartbeat events when page is inactive
- **Time-based Deduplication**: Combines events within 100ms window
- **Smart Batching**: Buffers events before storage for efficiency

### 3. **Advanced Dashboard**
- Visual workflow timeline
- Event grouping by sessions (5-minute gap threshold)
- Real-time statistics:
  - Total events captured
  - Number of workflows detected
  - Filtered/combined event count
  - Unique event types
- Color-coded filtered events
- Detailed event inspection with collapsible sections

### 4. **Data Export Capabilities**
Export your captured data in multiple formats:

#### **Export Events CSV**
- Flattened event structure
- All metadata included
- Timestamp-based filename

#### **Export Workflows CSV**
- Grouped by workflow sessions
- Includes workflow metadata (ID, sequence, total events)
- Easy analysis in Excel/spreadsheet tools

#### **Export Summary CSV**
- High-level statistics
- Event type breakdown
- URL frequency analysis
- Time range coverage

## 🛠️ Installation

1. Clone or download this repository
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable "Developer mode" (top right)
4. Click "Load unpacked"
5. Select the `extension` folder

## 📊 Usage

### Basic Operation
1. The extension starts capturing automatically once installed
2. Click the extension icon to access quick controls
3. Click "Open Dashboard" to view captured workflows

### Viewing Data
- **Workflows Panel (Left)**: Lists all detected workflow sessions
  - Green badge indicates noise-filtered workflows
- **Details Panel (Right)**: Shows detailed event information
  - Yellow badges show combined event counts

### Exporting Data
1. Open the dashboard
2. Use the export buttons in the header:
   - **Export Events CSV**: All raw events
   - **Export Workflows CSV**: Grouped by sessions
   - **Export Summary CSV**: Statistical overview

## 🧹 Noise Reduction Details

### What Gets Filtered?

| Event Type | Filter Criteria |
|------------|-----------------|
| Scroll | Movements < 50px from last scroll |
| Mouse Move | Movements < 20px from last position |
| Input | Rapid typing on same field (combined) |
| Focus/Blur | On insignificant DOM elements |
| Visibility | Changes within 1 second |
| Heartbeat | When page is hidden/inactive |

### Event Combining

Similar consecutive events are automatically merged:
- Scroll events within 100ms
- Input events on the same field
- Mouse movements in small area

Combined events show a badge indicating how many were merged (e.g., "Combined 5x")

## 📦 Data Storage

- **Technology**: IndexedDB (efficient for large datasets)
- **Database**: `TaskMiningDB`
- **Store**: `events` with auto-increment ID
- **Indexes**: 
  - `event_ts` (timestamp)
  - `event_type` (event name)
  - `url` (page URL)

## 🔧 Configuration

Edit constants in files to customize behavior:

### In `content.js`:
```javascript
const CAPTURE_INPUT_VALUE = false;  // Capture actual input values
const CAPTURE_INPUT_HASH = true;    // Hash input values (privacy)
```

### In `noiseReduction.js`:
```javascript
BUFFER_DELAY = 100;            // Event batching delay (ms)
SCROLL_THRESHOLD = 50;         // Minimum scroll distance (px)
MOUSE_MOVE_THRESHOLD = 20;     // Minimum mouse movement (px)
```

### In `dashboard.js`:
```javascript
const GAP = 5 * 60 * 1000;     // Workflow session gap (5 minutes)
```

## 🎯 Roadmap Compliance

This implementation follows **Section 2.6** of the project roadmap:

✅ Combine consecutive similar events  
✅ Ignore insignificant DOM nodes  
✅ Threshold scroll/mouse movement events  
✅ Batch events before writing  
✅ Idle-time segmentation (sessionizing)

## 🔐 Privacy Considerations

- Input values are **not stored by default** (unless enabled)
- Passwords are **never captured** (hashed only if enabled)
- All data stored **locally** in browser
- No external server communication
- User has full control over data export and deletion

## 📝 Event Schema

Each captured event contains:
```javascript
{
  event: "click",              // Event type
  timestamp: 1234567890,       // Unix timestamp
  url: "https://...",          // Page URL
  title: "Page Title",         // Page title
  viewport: {width, height},   // Viewport size
  scrollY: 100,                // Scroll position
  page_fingerprint: "...",     // Page identifier
  data: {                      // Event-specific data
    element_type: "button",
    css_selector: "...",
    xpath: "...",
    dom_context: {...},
    // ... more metadata
  },
  combinedCount: 3             // # of merged events (if applicable)
}
```

## 🐛 Troubleshooting

### Dashboard shows no data
- Check if content script is loading (console logs)
- Verify IndexedDB is enabled in browser
- Check for extension errors in `chrome://extensions/`

### Events not being captured
- Ensure extension has permissions for the site
- Check content script injection in DevTools > Sources
- Verify noise filter isn't too aggressive

### Export not working
- Check browser popup blockers
- Ensure download permissions are granted
- Try exporting smaller date ranges

## 📚 Development

### File Organization
All files are now properly organized in the `src/` directory:
- `background/`: Service worker logic
- `content/`: Page injection scripts  
- `ui/`: User interface components
- `utils/`: Shared utilities and helpers

### Adding New Event Listeners
1. Add listener in `content.js`
2. Use `buildEventObject()` helper
3. Call `safeSend()` to apply noise filtering
4. Update dashboard visualization if needed

### Customizing Noise Filters
Edit `src/utils/noiseReduction.js`:
- Modify `shouldFilterEvent()` for filtering logic
- Adjust `areSimilarEvents()` for combining logic
- Update thresholds in constructor

## 📄 License

See project root LICENSE file.

## 🤝 Contributing

1. Follow the existing code structure
2. Test with real workflows before committing
3. Update this README for significant changes
4. Ensure noise reduction doesn't filter important events

---

**Version**: 1.0  
**Last Updated**: December 23, 2025  
**Roadmap Compliance**: Section 2.6 (Noise Reduction & Prefiltering)
