/**
 * 暗黑模式设计系统
 * Dark Mode Design System
 */

// 颜色系统
export const colors = {
  // 背景色
  bgPrimary: '#0F0F0F',      // 页面主背景
  bgSecondary: '#1A1A1A',    // 卡片、面板背景
  bgTertiary: '#2D2D2D',     // 悬停、输入框背景
  bgQuaternary: '#3D3D3D',   // 选中、激活背景

  // 文字色
  textPrimary: '#FFFFFF',    // 主标题
  textSecondary: '#A0A0A0',  // 正文
  textTertiary: '#666666',   // 辅助文字
  textDisabled: '#444444',   // 禁用文字

  // 边框色
  borderPrimary: '#333333',  // 主要边框
  borderSecondary: '#444444', // 悬停边框
  borderTertiary: '#555555',  // 激活边框

  // 强调色 - 青绿
  accentPrimary: '#00D4AA',
  accentHover: '#00FFC2',
  accentPressed: '#00B894',
  accentMuted: 'rgba(0, 212, 170, 0.15)',

  // 功能色
  success: '#00C853',
  warning: '#FFB800',
  error: '#FF4D4D',
  info: '#3B82F6',
}

// 圆角系统
export const borderRadius = {
  sm: '6px',
  md: '8px',
  lg: '12px',
  xl: '16px',
  full: '9999px',
}

// 阴影系统
export const shadows = {
  sm: '0 2px 8px rgba(0, 0, 0, 0.3)',
  md: '0 4px 16px rgba(0, 0, 0, 0.4)',
  lg: '0 8px 32px rgba(0, 0, 0, 0.5)',
  glow: '0 0 20px rgba(0, 212, 170, 0.3)',
}

// Naive UI 暗黑主题配置
export const darkThemeOverrides = {
  common: {
    primaryColor: colors.accentPrimary,
    primaryColorHover: colors.accentHover,
    primaryColorPressed: colors.accentPressed,
    primaryColorSuppl: colors.accentMuted,

    successColor: colors.success,
    warningColor: colors.warning,
    errorColor: colors.error,
    infoColor: colors.info,

    textColorBase: colors.textPrimary,
    textColor1: colors.textPrimary,
    textColor2: colors.textSecondary,
    textColor3: colors.textTertiary,

    bodyColor: colors.bgPrimary,
    cardColor: colors.bgSecondary,
    modalColor: colors.bgSecondary,
    popoverColor: colors.bgTertiary,

    borderColor: colors.borderPrimary,
    dividerColor: colors.borderPrimary,
  },
}
