/**
 * Accessibility helper utilities and components
 */

/**
 * Skip to main content link for keyboard navigation
 */
export const SkipToMain = () => {
  return (
    <a
      href="#main-content"
      style={{
        position: 'absolute',
        left: '-9999px',
        zIndex: 999,
        padding: '1em',
        backgroundColor: '#1976d2',
        color: 'white',
        textDecoration: 'none',
        borderRadius: '0 0 4px 0',
      }}
      onFocus={(e) => {
        e.target.style.left = '0';
      }}
      onBlur={(e) => {
        e.target.style.left = '-9999px';
      }}
    >
      Skip to main content
    </a>
  );
};

/**
 * Live region for screen reader announcements
 */
export const LiveRegion = ({ message, ariaLive = 'polite' }) => {
  return (
    <div
      role="status"
      aria-live={ariaLive}
      aria-atomic="true"
      style={{
        position: 'absolute',
        left: '-9999px',
        width: '1px',
        height: '1px',
        overflow: 'hidden',
      }}
    >
      {message}
    </div>
  );
};

/**
 * Visually hidden text for screen readers only
 */
export const VisuallyHidden = ({ children }) => {
  return (
    <span
      style={{
        position: 'absolute',
        width: '1px',
        height: '1px',
        padding: 0,
        margin: '-1px',
        overflow: 'hidden',
        clip: 'rect(0,0,0,0)',
        whiteSpace: 'nowrap',
        border: 0,
      }}
    >
      {children}
    </span>
  );
};

/**
 * Focus trap utilities
 */
export const getFocusableElements = (container) => {
  return container.querySelectorAll(
    'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])'
  );
};

/**
 * Accessibility attributes for buttons
 */
export const buttonA11yProps = (label, pressed = false, expanded = false) => {
  return {
    'aria-label': label,
    'aria-pressed': pressed !== false ? pressed : undefined,
    'aria-expanded': expanded !== false ? expanded : undefined,
  };
};

/**
 * Accessibility attributes for tabs
 */
export const tabA11yProps = (index, id = 'tab') => {
  return {
    id: `${id}-${index}`,
    'aria-controls': `${id}panel-${index}`,
    role: 'tab',
    'aria-selected': false,
  };
};

/**
 * Accessibility attributes for tab panels
 */
export const tabPanelA11yProps = (index, id = 'tab') => {
  return {
    id: `${id}panel-${index}`,
    'aria-labelledby': `${id}-${index}`,
    role: 'tabpanel',
  };
};

/**
 * Check if element is visible to screen readers
 */
export const isVisible = (element) => {
  return (
    element.offsetWidth > 0 ||
    element.offsetHeight > 0 ||
    element.getClientRects().length > 0
  );
};

/**
 * Announce message to screen readers
 */
export const announceToScreenReader = (message, priority = 'polite') => {
  const announcement = document.createElement('div');
  announcement.setAttribute('role', 'status');
  announcement.setAttribute('aria-live', priority);
  announcement.setAttribute('aria-atomic', 'true');
  announcement.style.position = 'absolute';
  announcement.style.left = '-9999px';
  announcement.textContent = message;

  document.body.appendChild(announcement);

  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
};

export default {
  SkipToMain,
  LiveRegion,
  VisuallyHidden,
  getFocusableElements,
  buttonA11yProps,
  tabA11yProps,
  tabPanelA11yProps,
  isVisible,
  announceToScreenReader,
};
