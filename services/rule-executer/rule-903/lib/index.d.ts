// Minimal type declarations for the local Rule 903 implementation
// This prevents TypeScript errors during the container build where the
// runtime implementation is plain JS and no types are published.

import type { RuleRequest, RuleResult } from '@tazama-lf/frms-coe-lib/lib/interfaces';

declare function handleTransaction(
  req: RuleRequest & Record<string, any>,
  determineOutcome: (...args: any[]) => any,
  ruleResult: RuleResult,
  loggerService: any,
  ruleConfig: any,
  databaseManager: any,
): Promise<RuleResult>;

export { handleTransaction };
