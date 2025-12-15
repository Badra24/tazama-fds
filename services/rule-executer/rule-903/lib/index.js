"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.handleTransaction = handleTransaction;
/**
 * Main transaction handler for Rule 903: Geographic Risk Detection
 * Analyzes transaction geo-location data to determine risk level based on configured zones
 */
async function handleTransaction(req, determineOutcome, ruleResult, loggerService, ruleConfig, databaseManager) {
    loggerService.log('Rule 903 handleTransaction called', 'Rule 903');
    const config = ruleConfig;
    // Log transaction keys for debugging
    loggerService.log(`Transaction keys: ${Object.keys(req.transaction || {}).join(', ')}`, 'Rule 903');
    // Extract geo-location from transaction
    const geoLocation = extractGeoLocation(req, loggerService);
    if (!geoLocation || (!geoLocation.city && !geoLocation.region && !geoLocation.lat)) {
        // No geo-location data available - exit condition
        loggerService.log('No geo-location data found in transaction', 'Rule 903');
        return {
            ...ruleResult,
            subRuleRef: '.x00',
            reason: 'Geo-location data not available'
        };
    }
    // If we only have coordinates, try to determine city from them
    if (!geoLocation.city && !geoLocation.region && geoLocation.lat && geoLocation.long) {
        const cityFromCoords = getCityFromCoordinates(parseFloat(geoLocation.lat), parseFloat(geoLocation.long));
        if (cityFromCoords) {
            geoLocation.city = cityFromCoords;
            loggerService.log(`Determined city from coordinates: ${cityFromCoords}`, 'Rule 903');
        }
    }
    // Determine risk level based on location
    const riskLevel = determineRiskLevel(geoLocation, config);
    // Map risk level to band
    const bands = config.bands || ['.01', '.02', '.03'];
    const subRuleRef = bands[riskLevel] || '.x00';
    const riskZones = ['HIGH RISK', 'MEDIUM RISK', 'LOW RISK'];
    const reason = `Transaction from ${riskZones[riskLevel]} zone (${geoLocation.city || geoLocation.region})`;
    loggerService.log(reason, 'Rule 903');
    return {
        ...ruleResult,
        subRuleRef,
        reason,
        indpdntVarbl: riskLevel,
        transaction: req.transaction
    };
}
/**
 * Extract geo-location data from transaction
 * Supports pain.001, pacs.008, and pacs.002 message types
 * Returns null for missing values instead of undefined to prevent crashes
 */
function extractGeoLocation(req, logger) {
    try {
        // Path for pain.001: CstmrCdtTrfInitn.SplmtryData.Envlp.Doc.InitgPty.Glctn
        if ('CstmrCdtTrfInitn' in (req.transaction || {})) {
            const pain001Path = req.transaction.CstmrCdtTrfInitn?.SplmtryData;
            if (pain001Path && Array.isArray(pain001Path)) {
                for (const splmtry of pain001Path) {
                    const glctn = splmtry?.Envlp?.Doc?.InitgPty?.Glctn;
                    if (glctn) {
                        return {
                            city: glctn.City || null,
                            region: glctn.Region || null,
                            lat: glctn.Lat || null,
                            long: glctn.Long || null
                        };
                    }
                }
            }
        }
        // Path for pacs.008: FIToFICstmrCdtTrf.SplmtryData.Envlp.Doc.InitgPty.Glctn (outer level)
        if ('FIToFICstmrCdtTrf' in (req.transaction || {})) {
            const pacs008Outer = req.transaction.FIToFICstmrCdtTrf?.SplmtryData;
            if (pacs008Outer) {
                const glctn = pacs008Outer?.Envlp?.Doc?.InitgPty?.Glctn;
                if (glctn) {
                    return {
                        city: glctn.City || null,
                        region: glctn.Region || null,
                        lat: glctn.Lat || null,
                        long: glctn.Long || null
                    };
                }
            }
        }
        // Path for pacs.002: FIToFIPmtSts.SplmtryData.Envlp.Doc.InitgPty.Glctn (outer level)
        if ('FIToFIPmtSts' in (req.transaction || {})) {
            const pacs002Outer = req.transaction.FIToFIPmtSts?.SplmtryData;
            if (pacs002Outer) {
                const glctn = pacs002Outer?.Envlp?.Doc?.InitgPty?.Glctn;
                if (glctn) {
                    return {
                        city: glctn.City || null,
                        region: glctn.Region || null,
                        lat: glctn.Lat || null,
                        long: glctn.Long || null
                    };
                }
            }
        }
        // Also check inside CdtTrfTxInf.SplmtryData as fallback (pacs.008 inner path)
        let txInfoArray = [];
        if (req.transaction &&
            typeof req.transaction === 'object' &&
            'FIToFICstmrCdtTrf' in req.transaction &&
            req.transaction.FIToFICstmrCdtTrf &&
            Object.prototype.hasOwnProperty.call(req.transaction.FIToFICstmrCdtTrf, 'CdtTrfTxInf')) {
            const pacs008Inner = req.transaction.FIToFICstmrCdtTrf.CdtTrfTxInf;
            txInfoArray = Array.isArray(pacs008Inner) ? pacs008Inner : [pacs008Inner];
        }
        for (const txInfo of txInfoArray) {
            if (!txInfo)
                continue;
            const splmtryData = txInfo?.SplmtryData;
            const splmtryArray = Array.isArray(splmtryData) ? splmtryData : [splmtryData];
            for (const splmtry of splmtryArray) {
                if (!splmtry)
                    continue;
                const glctn = splmtry?.Envlp?.Doc?.InitgPty?.Glctn;
                if (glctn) {
                    return {
                        city: glctn.City || null,
                        region: glctn.Region || null,
                        lat: glctn.Lat || null,
                        long: glctn.Long || null
                    };
                }
            }
        }
        // Check inside TxInfAndSts.SplmtryData as fallback (pacs.002 inner path)
        if ('FIToFIPmtSts' in (req.transaction || {})) {
            const txInfAndSts = req.transaction.FIToFIPmtSts?.TxInfAndSts;
            const txInfArray = Array.isArray(txInfAndSts) ? txInfAndSts : [txInfAndSts];
            for (const txInf of txInfArray) {
                if (!txInf)
                    continue;
                const splmtryData = txInf?.SplmtryData;
                const splmtryArray = Array.isArray(splmtryData) ? splmtryData : [splmtryData];
                for (const splmtry of splmtryArray) {
                    if (!splmtry)
                        continue;
                    const glctn = splmtry?.Envlp?.Doc?.InitgPty?.Glctn;
                    if (glctn) {
                        return {
                            city: glctn.City || null,
                            region: glctn.Region || null,
                            lat: glctn.Lat || null,
                            long: glctn.Long || null
                        };
                    }
                }
            }
        }
        return null;
    }
    catch (error) {
        console.error('[Rule 903] Error extracting geo-location:', error);
        return null;
    }
}
/**
 * Determine risk level based on location and configuration
 * Returns: 0 (high risk), 1 (medium risk), 2 (low risk)
 */
function determineRiskLevel(location, config) {
    const city = location.city?.toLowerCase();
    const region = location.region?.toLowerCase();
    // Access riskZones from parameters (database structure) or directly from config
    const riskZones = config.config?.parameters?.riskZones || config.parameters?.riskZones || config.riskZones || {};
    // Check high risk zones (cities and regions)
    const highRiskCities = riskZones.high?.cities?.map((z) => z.toLowerCase()) || [];
    const highRiskRegions = riskZones.high?.regions?.map((z) => z.toLowerCase()) || [];
    if (city && highRiskCities.includes(city))
        return 0;
    if (region && highRiskRegions.includes(region))
        return 0;
    // Check medium risk zones (cities and regions)
    const mediumRiskCities = riskZones.medium?.cities?.map((z) => z.toLowerCase()) || [];
    const mediumRiskRegions = riskZones.medium?.regions?.map((z) => z.toLowerCase()) || [];
    if (city && mediumRiskCities.includes(city))
        return 1;
    if (region && mediumRiskRegions.includes(region))
        return 1;
    // Default to low risk
    return 2;
}
/**
 * Determine city from coordinates using approximate bounding boxes
 * Jakarta: ~-6.1° to -6.4° lat, 106.7° to 107.0° long
 * Surabaya: ~-7.2° to -7.4° lat, 112.6° to 112.8° long
 * Bandung: ~-6.9° to -7.0° lat, 107.5° to 107.7° long
 * Semarang: ~-6.9° to -7.1° lat, 110.3° to 110.5° long
 * Denpasar: ~-8.6° to -8.7° lat, 115.1° to 115.3° long
 * Tangerang: ~-6.1° to -6.3° lat, 106.6° to 106.8° long
 */
function getCityFromCoordinates(lat, long) {
    // Jakarta
    if (lat >= -6.4 && lat <= -6.1 && long >= 106.7 && long <= 107.0) {
        return 'Jakarta';
    }
    // Tangerang (west of Jakarta)
    if (lat >= -6.3 && lat <= -6.1 && long >= 106.6 && long <= 106.8) {
        return 'Tangerang';
    }
    // Surabaya
    if (lat >= -7.4 && lat <= -7.2 && long >= 112.6 && long <= 112.8) {
        return 'Surabaya';
    }
    // Bandung
    if (lat >= -7.0 && lat <= -6.9 && long >= 107.5 && long <= 107.7) {
        return 'Bandung';
    }
    // Semarang
    if (lat >= -7.1 && lat <= -6.9 && long >= 110.3 && long <= 110.5) {
        return 'Semarang';
    }
    // Denpasar
    if (lat >= -8.7 && lat <= -8.6 && long >= 115.1 && long <= 115.3) {
        return 'Denpasar';
    }
    return null;
}
