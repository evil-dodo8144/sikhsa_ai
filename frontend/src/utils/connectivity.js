export const checkConnectivity = async () => {
  try {
    const response = await fetch('https://api.scaledown.ai/health', {
      method: 'HEAD',
      mode: 'no-cors',
      cache: 'no-cache',
      timeout: 5000
    });
    return true;
  } catch (error) {
    return false;
  }
};

export const getConnectionType = () => {
  if ('connection' in navigator) {
    const connection = navigator.connection ||
      navigator.mozConnection ||
      navigator.webkitConnection;
    
    return {
      type: connection.effectiveType,
      downlink: connection.downlink,
      rtt: connection.rtt,
      saveData: connection.saveData
    };
  }
  
  return {
    type: 'unknown',
    downlink: null,
    rtt: null,
    saveData: false
  };
};

export const isSlowConnection = () => {
  const conn = getConnectionType();
  return conn.type === 'slow-2g' || conn.type === '2g' || conn.saveData;
};

export const onConnectivityChange = (callback) => {
  window.addEventListener('online', () => callback(true));
  window.addEventListener('offline', () => callback(false));
  
  if ('connection' in navigator) {
    navigator.connection.addEventListener('change', () => {
      callback(navigator.onLine);
    });
  }
};