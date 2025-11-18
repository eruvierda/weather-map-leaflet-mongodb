/**
 * Smart Cache Manager for Weather Data
 * Balances performance with data freshness
 * 
 * Features:
 * - Intelligent caching based on data type and age
 * - Background refresh for better UX
 * - Fallback to cached data if fresh fetch fails
 * - Memory and localStorage optimization
 */

class SmartCacheManager {
    constructor() {
        this.cache = new Map();
        this.baseApiUrl = (window.WEATHER_API_BASE || '').replace(/\/$/, '') || '';
        this.cacheConfig = {
            // Weather data: cache for shorter periods
            weather: {
                maxAge: 30 * 60 * 1000, // 30 minutes
                backgroundRefresh: true,
                priority: 'high'
            },
            // Static data: cache for longer periods
            static: {
                maxAge: 24 * 60 * 60 * 1000, // 24 hours
                backgroundRefresh: false,
                priority: 'low'
            },
            // Grid data: cache for medium periods
            grid: {
                maxAge: 2 * 60 * 60 * 1000, // 2 hours
                backgroundRefresh: true,
                priority: 'medium'
            }
        };
        
        this.init();
    }
    
    init() {
        // Initialize metadata cache
        this.metadataCache = {};
        
        // Load cached data from localStorage
        this.loadFromStorage();
        
        // Setup periodic cache cleanup
        setInterval(() => this.cleanup(), 5 * 60 * 1000); // Every 5 minutes
        
        // Setup storage error recovery
        this.setupStorageErrorRecovery();
    }
    
    /**
     * Setup storage error recovery
     */
    setupStorageErrorRecovery() {
        // Listen for storage errors
        window.addEventListener('storage', (e) => {
            if (e.key === 'weatherCache' && e.newValue === null) {
                console.warn('⚠️ localStorage was cleared externally, resetting cache');
                this.metadataCache = {};
            }
        });
        
        // Handle quota exceeded errors globally
        window.addEventListener('error', (e) => {
            if (e.error && e.error.name === 'QuotaExceededError') {
                console.warn('🚨 Global storage quota exceeded, clearing cache');
                this.clearLocalStorage();
            }
        });
    }
    
    /**
     * Get data with smart caching and large data handling
     */
    buildUrl(resource) {
        if (!resource.startsWith('http')) {
            return `${this.baseApiUrl}${resource.startsWith('/') ? '' : '/'}${resource}`;
        }
        return resource;
    }

    async getData(resource, type = 'weather', forceRefresh = false) {
        const url = this.buildUrl(resource);
        const cacheKey = this.generateCacheKey(url);
        const config = this.cacheConfig[type] || this.cacheConfig.weather;
        
        // Check if we have valid cached data
        if (!forceRefresh && this.isCacheValid(cacheKey, config.maxAge)) {
            const cachedData = this.getFromCache(cacheKey);
            if (cachedData) {
                console.log(`📦 Using cached ${type} data for: ${url}`);
                
                // Background refresh if enabled
                if (config.backgroundRefresh) {
                    this.backgroundRefresh(url, type, cacheKey);
                }
                
                return cachedData;
            }
        }
        
        // Fetch fresh data
        try {
            console.log(`🔄 Fetching fresh ${type} data for: ${url}`);
            const freshData = await this.fetchWithCacheBuster(url);
            
            // Check if data is too large for caching
            const dataSize = JSON.stringify(freshData).length;
            const maxCacheSize = 10 * 1024 * 1024; // 10MB limit
            
            if (dataSize > maxCacheSize) {
                console.warn(`⚠️ Data too large (${(dataSize / 1024 / 1024).toFixed(2)} MB), not caching: ${url}`);
                // Store only metadata for large data
                this.setCacheMetadata(cacheKey, freshData, type, dataSize);
            } else {
                // Cache the fresh data normally
                this.setCache(cacheKey, freshData, type);
            }
            
            return freshData;
            
        } catch (error) {
            console.warn(`❌ Failed to fetch fresh data for ${url}:`, error);
            
            // Fallback to cached data if available
            const fallbackData = this.getFromCache(cacheKey);
            if (fallbackData) {
                console.log(`🔄 Using fallback cached data for: ${url}`);
                return fallbackData;
            }
            
            throw error;
        }
    }
    
    /**
     * Background refresh for better UX
     */
    async backgroundRefresh(url, type, cacheKey) {
        try {
            const freshData = await this.fetchWithCacheBuster(url);
            this.setCache(cacheKey, freshData, type);
            console.log(`🔄 Background refresh completed for: ${url}`);
        } catch (error) {
            console.warn(`❌ Background refresh failed for ${url}:`, error);
        }
    }
    
    /**
     * Fetch data with cache-busting
     */
    async fetchWithCacheBuster(url) {
        const cacheBuster = `_t=${Date.now()}`;
        const separator = url.includes('?') ? '&' : '?';
        const fullUrl = `${url}${separator}${cacheBuster}`;
        
        const response = await fetch(fullUrl, {
            cache: 'no-cache',
            headers: {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        return await response.json();
    }
    
    /**
     * Check if cache is still valid
     */
    isCacheValid(cacheKey, maxAge) {
        const cached = this.cache.get(cacheKey);
        if (!cached) return false;
        
        const age = Date.now() - cached.timestamp;
        return age < maxAge;
    }
    
    /**
     * Get data from cache
     */
    getFromCache(cacheKey) {
        const cached = this.cache.get(cacheKey);
        if (!cached) return null;
        
        // If this is metadata-only (large data), return null to force fresh fetch
        if (cached.isMetadata) {
            console.log(`📋 Found metadata-only cache for ${cacheKey}, will fetch fresh data`);
            return null;
        }
        
        return cached.data;
    }
    
    /**
     * Set data in cache with memory management
     */
    setCache(cacheKey, data, type) {
        const config = this.cacheConfig[type] || this.cacheConfig.weather;
        
        // Check memory usage before adding new data
        const dataSize = JSON.stringify(data).length;
        const maxMemoryMB = 50; // Maximum 50MB for cache
        
        if (this.getCurrentMemoryUsage() + dataSize > maxMemoryMB * 1024 * 1024) {
            console.warn(`⚠️ Memory limit approaching, clearing old entries before caching ${cacheKey}`);
            this.clearOldestEntries();
        }
        
        this.cache.set(cacheKey, {
            data: data,
            timestamp: Date.now(),
            type: type,
            priority: config.priority,
            size: dataSize
        });
        
        // Also save to localStorage for persistence
        this.saveToStorage();
        
        console.log(`💾 Cached ${type} data for: ${cacheKey} (${(dataSize / 1024).toFixed(2)} KB)`);
    }
    
    /**
     * Set cache metadata for large data (without storing the actual data)
     */
    setCacheMetadata(cacheKey, data, type, dataSize) {
        const config = this.cacheConfig[type] || this.cacheConfig.weather;
        
        this.cache.set(cacheKey, {
            data: null, // Don't store large data
            timestamp: Date.now(),
            type: type,
            priority: config.priority,
            size: dataSize,
            isMetadata: true,
            dataHash: this.generateDataHash(data)
        });
        
        console.log(`📋 Cached metadata for large ${type} data: ${cacheKey} (${(dataSize / 1024 / 1024).toFixed(2)} MB)`);
    }
    
    /**
     * Generate cache key from URL
     */
    generateCacheKey(url) {
        // Remove cache-busting parameters
        return url.split('?')[0].split('&')[0];
    }
    
    /**
     * Save cache to localStorage with smart storage management
     */
    saveToStorage() {
        try {
            // Check available storage space
            const availableSpace = this.getAvailableStorageSpace();
            console.log(`📦 Available storage space: ${availableSpace} MB`);
            
            // Get cache data and estimate size
            const cacheData = {};
            let totalSize = 0;
            
            for (const [key, value] of this.cache.entries()) {
                // Only store essential data to save space
                const essentialData = {
                    timestamp: value.timestamp,
                    type: value.type,
                    priority: value.priority,
                    // Store only metadata for large data, not the full data
                    dataSize: JSON.stringify(value.data).length,
                    dataHash: this.generateDataHash(value.data)
                };
                
                cacheData[key] = essentialData;
                totalSize += JSON.stringify(essentialData).length;
            }
            
            // Check if we have enough space
            if (totalSize > availableSpace * 1024 * 1024 * 0.8) { // 80% of available space
                console.warn('⚠️ Cache too large for localStorage, clearing old entries');
                this.clearOldestEntries();
                return this.saveToStorage(); // Retry with reduced cache
            }
            
            localStorage.setItem('weatherCache', JSON.stringify(cacheData));
            console.log(`💾 Cache metadata saved to localStorage (${(totalSize / 1024).toFixed(2)} KB)`);
            
        } catch (error) {
            if (error.name === 'QuotaExceededError') {
                console.warn('🚨 localStorage quota exceeded, clearing old entries and retrying');
                this.clearOldestEntries();
                this.saveToStorage(); // Retry
            } else {
                console.warn('Failed to save cache to localStorage:', error);
            }
        }
    }
    
    /**
     * Load cache from localStorage (metadata only)
     */
    loadFromStorage() {
        try {
            const cached = localStorage.getItem('weatherCache');
            if (cached) {
                const cacheData = JSON.parse(cached);
                console.log(`📦 Loaded ${Object.keys(cacheData).length} cache metadata entries from localStorage`);
                
                // Note: We only load metadata, not the actual data
                // Data will be fetched fresh when needed
                this.metadataCache = cacheData;
            }
        } catch (error) {
            console.warn('Failed to load cache metadata from localStorage:', error);
        }
    }
    
    /**
     * Get available storage space in MB
     */
    getAvailableStorageSpace() {
        try {
            const testKey = '__storage_test__';
            const testValue = 'x'.repeat(1024 * 1024); // 1MB test
            
            // Try to store progressively larger data to find available space
            for (let size = 1; size <= 50; size++) {
                try {
                    localStorage.setItem(testKey, 'x'.repeat(size * 1024 * 1024));
                    localStorage.removeItem(testKey);
                } catch (e) {
                    return size - 1; // Return available space in MB
                }
            }
            return 50; // Default to 50MB if we can't determine
        } catch (error) {
            console.warn('Could not determine available storage space:', error);
            return 5; // Conservative default
        }
    }
    
    /**
     * Generate a simple hash for data integrity checking
     */
    generateDataHash(data) {
        try {
            const str = JSON.stringify(data);
            let hash = 0;
            for (let i = 0; i < str.length; i++) {
                const char = str.charCodeAt(i);
                hash = ((hash << 5) - hash) + char;
                hash = hash & hash; // Convert to 32-bit integer
            }
            return hash.toString(36);
        } catch (error) {
            return '0';
        }
    }
    
    /**
     * Clear oldest cache entries when storage is full
     */
    clearOldestEntries() {
        const entries = Array.from(this.cache.entries());
        
        // Sort by timestamp (oldest first)
        entries.sort((a, b) => a[1].timestamp - b[1].timestamp);
        
        // Remove oldest 25% of entries
        const removeCount = Math.ceil(entries.length * 0.25);
        let removed = 0;
        
        for (let i = 0; i < removeCount && i < entries.length; i++) {
            this.cache.delete(entries[i][0]);
            removed++;
        }
        
        console.log(`🧹 Cleared ${removed} oldest cache entries to free storage space`);
    }
    
    /**
     * Clean up expired cache entries
     */
    cleanup() {
        const now = Date.now();
        let cleaned = 0;
        
        for (const [key, value] of this.cache.entries()) {
            const config = this.cacheConfig[value.type] || this.cacheConfig.weather;
            if (now - value.timestamp > config.maxAge * 2) { // 2x max age
                this.cache.delete(key);
                cleaned++;
            }
        }
        
        if (cleaned > 0) {
            console.log(`🧹 Cleaned up ${cleaned} expired cache entries`);
            this.saveToStorage();
        }
    }
    
    /**
     * Get cache statistics
     */
    getStats() {
        const stats = {
            total: this.cache.size,
            byType: {},
            memoryUsage: this.getCurrentMemoryUsage(),
            storageInfo: this.getStorageInfo()
        };
        
        for (const [key, value] of this.cache.entries()) {
            if (!stats.byType[value.type]) {
                stats.byType[value.type] = 0;
            }
            stats.byType[value.type]++;
        }
        
        return stats;
    }
    
    /**
     * Get current memory usage in MB
     */
    getCurrentMemoryUsage() {
        let totalSize = 0;
        for (const [key, value] of this.cache.entries()) {
            totalSize += value.size || JSON.stringify(value.data).length;
        }
        return (totalSize / 1024 / 1024).toFixed(2); // MB
    }
    
    /**
     * Get storage information
     */
    getStorageInfo() {
        try {
            const available = this.getAvailableStorageSpace();
            const used = this.getCurrentMemoryUsage();
            return {
                available: `${available} MB`,
                used: `${used} MB`,
                percentage: ((used / available) * 100).toFixed(1) + '%'
            };
        } catch (error) {
            return { available: 'Unknown', used: 'Unknown', percentage: 'Unknown' };
        }
    }
    
    /**
     * Clear all cache
     */
    clearCache() {
        this.cache.clear();
        this.metadataCache = {};
        localStorage.removeItem('weatherCache');
        console.log('🗑️ Cache cleared');
    }
    
    /**
     * Clear localStorage and reset storage management
     */
    clearLocalStorage() {
        try {
            localStorage.removeItem('weatherCache');
            this.metadataCache = {};
            console.log('🗑️ localStorage cleared');
        } catch (error) {
            console.warn('Failed to clear localStorage:', error);
        }
    }
    
    /**
     * Preload critical data
     */
    async preloadCriticalData() {
        const criticalUrls = [
            'pelabuhan/pelabuhan_weather_data.json',
            'openmeteo/city_weather_data.json',
            'openmeteo/grid_weather_data_1degree.json'
        ];
        
        console.log('🚀 Preloading critical weather data...');
        
        for (const url of criticalUrls) {
            try {
                await this.getData(url, 'weather', false);
            } catch (error) {
                console.warn(`Failed to preload ${url}:`, error);
            }
        }
        
        console.log('✅ Critical data preloading completed');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SmartCacheManager;
}
