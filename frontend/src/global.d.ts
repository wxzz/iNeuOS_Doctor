// 声明 window.VITE_GLOB_API_URL 以消除 TS 报错
interface Window {
  VITE_GLOB_API_URL: string;
  VERSION?: string;
}
