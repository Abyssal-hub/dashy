/**
 * React Hook for Interaction Tracking
 * 
 * Provides a hook for manual tracking of user interactions in React components.
 * 
 * Related: DEV-015, ARCHITECTURE.md Section 11.2.2
 */

"use client";

import { useCallback, useRef, useEffect } from "react";
import { logger, InteractionType, InteractionTarget } from "@/lib/logger";

export interface UseInteractionOptions {
  /** Track on mount (for component-level tracking) */
  trackMount?: boolean;
  /** Metadata generator function */
  getMetadata?: () => Record<string, any>;
}

export interface UseInteractionReturn {
  /** Start tracking an interaction */
  start: (type: InteractionType, target: Omit<InteractionTarget, "route">) => string;
  /** End tracking with optional error */
  end: (interactionId: string, error?: string) => void;
  /** Cancel without logging */
  cancel: (interactionId: string) => void;
  /** Track async operation */
  track: <T>(
    type: InteractionType,
    target: Omit<InteractionTarget, "route">,
    operation: () => Promise<T>
  ) => Promise<T>;
  /** Track sync operation */
  trackSync: <T>(
    type: InteractionType,
    target: Omit<InteractionTarget, "route">,
    operation: () => T
  ) => T;
}

/**
 * React hook for tracking user interactions
 * 
 * Usage:
 *   function MyComponent() {
 *     const { start, end, track } = useInteraction();
 *     
 *     const handleClick = async () => {
 *       const id = start('click', { element: 'btn-submit', component: 'MyComponent' });
 *       try {
 *         await submit();
 *         end(id);
 *       } catch (e) {
 *         end(id, String(e));
 *       }
 *     };
 *   }
 * 
 *   // Or with automatic tracking:
 *   const handleClick = () => track('click', { element: 'btn', component: 'Form' }, async () => {
 *     await submitForm();
 *   });
 */
export function useInteraction(options: UseInteractionOptions = {}): UseInteractionReturn {
  const interactionIdsRef = useRef<Set<string>>(new Set());

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      // Cancel any pending interactions
      interactionIdsRef.current.forEach((id) => logger.cancel(id));
      interactionIdsRef.current.clear();
    };
  }, []);

  const start = useCallback(
    (type: InteractionType, target: Omit<InteractionTarget, "route">): string => {
      const metadata = options.getMetadata?.();
      const id = logger.start(type, target, metadata);
      interactionIdsRef.current.add(id);
      return id;
    },
    [options.getMetadata]
  );

  const end = useCallback((interactionId: string, error?: string): void => {
    logger.end(interactionId, error);
    interactionIdsRef.current.delete(interactionId);
  }, []);

  const cancel = useCallback((interactionId: string): void => {
    logger.cancel(interactionId);
    interactionIdsRef.current.delete(interactionId);
  }, []);

  const track = useCallback(
    async <T,>(
      type: InteractionType,
      target: Omit<InteractionTarget, "route">,
      operation: () => Promise<T>
    ): Promise<T> => {
      const id = start(type, target);
      try {
        const result = await operation();
        end(id);
        return result;
      } catch (error) {
        end(id, String(error));
        throw error;
      }
    },
    [start, end]
  );

  const trackSync = useCallback(
    <T,>(
      type: InteractionType,
      target: Omit<InteractionTarget, "route">,
      operation: () => T
    ): T => {
      const id = start(type, target);
      try {
        const result = operation();
        end(id);
        return result;
      } catch (error) {
        end(id, String(error));
        throw error;
      }
    },
    [start, end]
  );

  return { start, end, cancel, track, trackSync };
}
