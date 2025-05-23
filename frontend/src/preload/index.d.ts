import { ElectronAPI } from '@electron-toolkit/preload'

declare global {
  interface Window {
    electron: ElectronAPI
    api: {
      openFolder: (filePath: string) => Promise<void>
      selectDirectory: () => Promise<string | undefined>
    }
  }
}
