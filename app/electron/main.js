import { app, BrowserWindow } from 'electron';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

let mainWindow = null;
let pendingDeepLink = null;

// Register custom protocol (with dev mode support for macOS)
if (!app.isDefaultProtocolClient('autoos')) {
  if (process.defaultApp && process.argv.length >= 2) {
    app.setAsDefaultProtocolClient('autoos', process.execPath, [path.resolve(process.argv[1])]);
  } else {
    app.setAsDefaultProtocolClient('autoos');
  }
}

function getBaseURL() {
  if (process.env.NODE_ENV === 'development' || !app.isPackaged) {
    return 'http://localhost:5173';
  }
  return null; // will use loadFile instead
}

// Convert autoos://share?blob=XXX into http://localhost:5173/?blob=XXX
function deepLinkToAppURL(deepLink) {
  try {
    const parsed = new URL(deepLink);
    const blob = parsed.searchParams.get('blob');
    const data = parsed.searchParams.get('data');
    
    const base = getBaseURL();
    if (base) {
      const params = new URLSearchParams();
      if (blob) params.set('blob', blob);
      if (data) params.set('data', data);
      return `${base}/?${params.toString()}`;
    }
    return null;
  } catch (e) {
    console.error('Failed to parse deep link:', e);
    return null;
  }
}

function createWindow(deepLink) {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      nodeIntegration: false,
      contextIsolation: true,
    },
  });

  // Allow window.open to create native popups
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    return {
      action: 'allow',
      overrideBrowserWindowOptions: {
        width: 420,
        height: 480,
        autoHideMenuBar: true,
        alwaysOnTop: true,
        webPreferences: {
          nodeIntegration: false,
          contextIsolation: true,
          preload: path.join(__dirname, 'preload.js'),
        }
      }
    };
  });

  // If we have a deep link, load the app with query params
  const appURL = deepLink ? deepLinkToAppURL(deepLink) : null;
  
  if (process.env.NODE_ENV === 'development' || !app.isPackaged) {
    mainWindow.loadURL(appURL || 'http://localhost:5173');
  } else {
    mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
  }
}

// Catch deep links that arrive BEFORE the app is ready
app.on('open-url', (event, url) => {
  event.preventDefault();
  
  if (mainWindow) {
    // App is already open — just navigate
    const appURL = deepLinkToAppURL(url);
    if (appURL) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
      mainWindow.loadURL(appURL);
    }
  } else {
    // App not ready yet — store for later
    pendingDeepLink = url;
  }
});

app.whenReady().then(() => {
  // Use pending deep link if one arrived before ready
  createWindow(pendingDeepLink);
  pendingDeepLink = null;

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});
