import type { Platform, PlatformAudio, PlatformFilesystem, PlatformLifecycle, PlatformMetadata, PlatformUpdater, UpdateStatus } from './types';

function noop(): void {}

const stubUpdaterStatus: UpdateStatus = {
  checking: false,
  available: false,
  downloading: false,
  installing: false,
  readyToInstall: false,
};

const stubUpdater: PlatformUpdater = {
  async checkForUpdates() { noop(); },
  async downloadAndInstall() { noop(); },
  async restartAndInstall() { noop(); },
  getStatus() { return stubUpdaterStatus; },
  subscribe() { return noop; },
};

const stubFilesystem: PlatformFilesystem = {
  async saveFile(filename, blob) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
    URL.revokeObjectURL(url);
  },
  async openPath(_path) { noop(); },
  async pickDirectory(_title) { return null; },
};

const stubAudio: PlatformAudio = {
  async isSystemAudioSupported() { return false; },
  async startSystemAudioCapture(_maxDurationSecs) { noop(); },
  async stopSystemAudioCapture() { throw new Error('System audio capture not supported in web'); },
  async listOutputDevices() { return []; },
  async playToDevices(_audioData, _deviceIds) { noop(); },
  stopPlayback() { noop(); },
};

const stubLifecycle: PlatformLifecycle = {
  async startServer(_remote, _modelsDir) { throw new Error('Server start not supported in web'); },
  async stopServer() { noop(); },
  async restartServer(_modelsDir) { throw new Error('Server restart not supported in web'); },
  async setKeepServerRunning(_keep) { noop(); },
  async setupWindowCloseHandler() { noop(); },
  subscribeToServerLogs() { return noop; },
};

const stubMetadata: PlatformMetadata = {
  async getVersion() { return '0.0.0'; },
  isTauri: false,
};

export const webPlatform: Platform = {
  filesystem: stubFilesystem,
  updater: stubUpdater,
  audio: stubAudio,
  lifecycle: stubLifecycle,
  metadata: stubMetadata,
};
