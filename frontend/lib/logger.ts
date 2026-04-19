/**
 * Frontend Interaction Logger Service
 * 
 * Provides logging for every start and end of user interaction on the UI.
 * Helps catch bugs by tracking user actions with timing and error context.
 * 
 * Related: DEV-015, ARCHITECTURE.md Section 11.2.2
 */

// Interaction types supported
export type InteractionType = 
  | "click" 
  | "hover" 
  | "scroll" 
  | "input" 
  | "navigation" 
  | "api_call";

// Target element information
export interface InteractionTarget {
  element: string;      // DOM element identifier (e.g., 'button', 'input#search')
  component: string;    // React component name
  route: string;        // Current page route (e.g., '/dashboard')
}

// Interaction log entry
export interface InteractionLog {
  interactionId: string;
  userId: string;
  sessionId: string;
  type: InteractionType;
  target: InteractionTarget;
  startedAt: string;    // ISO 8601
  endedAt?: string;     // ISO 8601
  duration?: number;    // milliseconds
  success: boolean;
  error?: string;
  metadata?: Record<string, any>;
}

// Logger configuration
export interface LoggerConfig {
  apiUrl: string;
  enabled: boolean;
}

/**
 * Logger for tracking user interactions on the UI.
 * 
 * Usage:
 *   const logger = new InteractionLogger();
 *   const id = logger.start('click', { element: 'btn-save', component: 'SettingsForm' });
 *   try {
 *     await saveSettings();
 *     logger.end(id);
 *   } catch (e) {
 *     logger.end(id, String(e));
 *   }
 */
export class InteractionLogger {
  private pending = new Map<string, InteractionLog>();
  private sessionId: string;
  private userId: string = "anonymous";
  private config: LoggerConfig;

  constructor(config: Partial<LoggerConfig> = {}) {
    this.config = {
      apiUrl: "/api/logs/interaction",
      enabled: true,
      ...config,
    };
    this.sessionId = this.getOrCreateSessionId();
  }

  /**
   * Set user ID after authentication
   */
  setUserId(userId: string): void {
    this.userId = userId;
  }

  /**
   * Start tracking an interaction
   * 
   * @param type - Type of interaction
   * @param target - Target element info (element, component). Route auto-detected.
   * @param metadata - Optional additional context
   * @returns interactionId - Use this to call end()
   */
  start(
    type: InteractionType,
    target: Omit<InteractionTarget, "route">,
    metadata?: Record<string, any>
  ): string {
    const interactionId = this.generateId();
    
    const log: InteractionLog = {
      interactionId,
      userId: this.userId,
      sessionId: this.sessionId,
      type,
      target: {
        ...target,
        route: this.getCurrentRoute(),
      },
      startedAt: new Date().toISOString(),
      success: true,
      metadata,
    };

    this.pending.set(interactionId, log);
    return interactionId;
  }

  /**
   * End tracking an interaction
   * 
   * @param interactionId - ID from start()
   * @param error - Error message if failed
   */
  end(interactionId: string, error?: string): void {
    const log = this.pending.get(interactionId);
    if (!log) return;

    log.endedAt = new Date().toISOString();
    log.duration = this.calculateDuration(log);
    log.success = !error;
    log.error = error;

    this.flush(log);
    this.pending.delete(interactionId);
  }

  /**
   * Cancel a pending interaction without logging
   */
  cancel(interactionId: string): void {
    this.pending.delete(interactionId);
  }

  /**
   * Track an interaction with automatic end (for async operations)
   * 
   * @param type - Interaction type
   * @param target - Target info
   * @param operation - Async function to track
   * @returns Result of the operation
   */
  async track<T>(
    type: InteractionType,
    target: Omit<InteractionTarget, "route">,
    operation: () => Promise<T>,
    metadata?: Record<string, any>
  ): Promise<T> {
    const id = this.start(type, target, metadata);
    try {
      const result = await operation();
      this.end(id);
      return result;
    } catch (error) {
      this.end(id, String(error));
      throw error;
    }
  }

  /**
   * Track a simple synchronous interaction
   */
  trackSync<T>(
    type: InteractionType,
    target: Omit<InteractionTarget, "route">,
    operation: () => T,
    metadata?: Record<string, any>
  ): T {
    const id = this.start(type, target, metadata);
    try {
      const result = operation();
      this.end(id);
      return result;
    } catch (error) {
      this.end(id, String(error));
      throw error;
    }
  }

  private generateId(): string {
    return `int_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  private getOrCreateSessionId(): string {
    if (typeof window === "undefined") return "server";
    
    let sessionId = sessionStorage.getItem("dashy_session_id");
    if (!sessionId) {
      sessionId = `sess_${Math.random().toString(36).substr(2, 16)}`;
      sessionStorage.setItem("dashy_session_id", sessionId);
    }
    return sessionId;
  }

  private getCurrentRoute(): string {
    if (typeof window === "undefined") return "/server";
    return window.location.pathname;
  }

  private calculateDuration(log: InteractionLog): number {
    const start = new Date(log.startedAt).getTime();
    const end = new Date().getTime();
    return end - start;
  }

  private flush(log: InteractionLog): void {
    if (!this.config.enabled) return;

    const payload = JSON.stringify(log);

    // Use sendBeacon for reliable delivery on page unload
    if (navigator.sendBeacon) {
      navigator.sendBeacon(this.config.apiUrl, new Blob([payload], { type: "application/json" }));
    } else {
      // Fallback to fetch with keepalive
      fetch(this.config.apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: payload,
        keepalive: true,
      }).catch(() => {
        // Silently fail - don't break UI on logging errors
      });
    }
  }
}

// Global logger instance
export const logger = new InteractionLogger();
