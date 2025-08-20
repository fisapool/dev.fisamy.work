/**
 * Safe JSON serialization utilities to handle circular references
 */

/**
 * Safely stringify an object, handling circular references
 * @param {any} obj - The object to stringify
 * @param {number|string} space - Optional spacing for pretty printing
 * @returns {string} JSON string with circular references marked
 */
export function safeStringify(obj, space) {
  const seen = new WeakSet();
  
  return JSON.stringify(obj, (key, value) => {
    if (typeof value === 'object' && value !== null) {
      if (seen.has(value)) {
        return '[Circular Reference]';
      }
      seen.add(value);
    }
    return value;
  }, space);
}

/**
 * Safely log an object to console, handling circular references
 * @param {any} obj - The object to log
 * @param {string} label - Optional label for the log
 */
export function safeLog(obj, label) {
  try {
    if (label) {
      console.log(label, obj);
    } else {
      console.log(obj);
    }
  } catch (error) {
    if (error instanceof Error && error.message.includes('circular structure')) {
      console.log(label || 'Object', '[Circular Reference - Object cannot be logged directly]');
      console.log('Object keys:', Object.keys(obj || {}));
      console.log('Object type:', typeof obj);
    } else {
      console.error('Error logging object:', error);
    }
  }
}

/**
 * Deep clone an object while handling circular references
 * @param {any} obj - The object to clone
 * @returns {any} A new object without circular references
 */
export function safeClone(obj) {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }
  
  if (obj instanceof Date) {
    return new Date(obj.getTime());
  }
  
  if (obj instanceof Array) {
    return obj.map(item => safeClone(item));
  }
  
  if (typeof obj === 'object') {
    const cloned = {};
    const seen = new WeakMap();
    
    const cloneRecursive = (current) => {
      if (current === null || typeof current !== 'object') {
        return current;
      }
      
      if (seen.has(current)) {
        return seen.get(current);
      }
      
      if (current instanceof Date) {
        return new Date(current.getTime());
      }
      
      if (current instanceof Array) {
        const clonedArray = current.map(item => cloneRecursive(item));
        seen.set(current, clonedArray);
        return clonedArray;
      }
      
      const clonedObj = {};
      seen.set(current, clonedObj);
      
      for (const key in current) {
        if (current.hasOwnProperty(key)) {
          clonedObj[key] = cloneRecursive(current[key]);
        }
      }
      
      return clonedObj;
    };
    
    return cloneRecursive(obj);
  }
  
  return obj;
}

/**
 * Check if an object has circular references
 * @param {any} obj - The object to check
 * @returns {boolean} True if circular references are detected
 */
export function hasCircularReferences(obj) {
  const seen = new WeakSet();
  
  function checkCircular(current) {
    if (current === null || typeof current !== 'object') {
      return false;
    }
    
    if (seen.has(current)) {
      return true;
    }
    
    seen.add(current);
    
    if (current instanceof Array) {
      return current.some(item => checkCircular(item));
    }
    
    for (const key in current) {
      if (current.hasOwnProperty(key)) {
        if (checkCircular(current[key])) {
          return true;
        }
      }
    }
    
    return false;
  }
  
  return checkCircular(obj);
}
