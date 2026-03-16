// Simple string compression for client-side storage
export const compress = (str) => {
  if (!str) return str;
  
  try {
    // Use btoa for base64 encoding (simple compression)
    return btoa(unescape(encodeURIComponent(str)));
  } catch (error) {
    console.error('Compression failed:', error);
    return str;
  }
};

export const decompress = (str) => {
  if (!str) return str;
  
  try {
    return decodeURIComponent(escape(atob(str)));
  } catch (error) {
    console.error('Decompression failed:', error);
    return str;
  }
};

// Estimate size savings
export const getCompressionRatio = (original, compressed) => {
  const originalSize = new Blob([original]).size;
  const compressedSize = new Blob([compressed]).size;
  return ((originalSize - compressedSize) / originalSize * 100).toFixed(1);
};