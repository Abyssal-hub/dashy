/**
 * Higher-Order Component for Automatic Interaction Tracking
 * 
 * Wraps components to automatically track mount/unmount lifecycle.
 * 
 * Related: DEV-015, ARCHITECTURE.md Section 11.2.2
 */

"use client";

import React, { useEffect, useRef } from "react";
import { logger, InteractionType } from "@/lib/logger";

export interface WithTrackingOptions {
  /** Type of interaction to log */
  type?: InteractionType;
  /** Component name for tracking */
  name?: string;
  /** Whether to track mount/unmount */
  trackLifecycle?: boolean;
  /** Whether to track all clicks within the component */
  trackClicks?: boolean;
  /** Metadata to include with all logs */
  metadata?: Record<string, any>;
}

/**
 * Higher-order component that adds automatic interaction tracking
 * 
 * Usage:
 *   // Automatic lifecycle tracking
 *   const TrackedDashboard = withInteractionTracking(Dashboard, {
 *     type: 'navigation',
 *     name: 'Dashboard',
 *     trackLifecycle: true,
 *   });
 * 
 *   // With click tracking
 *   const TrackedForm = withInteractionTracking(SettingsForm, {
 *     type: 'click',
 *     name: 'SettingsForm',
 *     trackClicks: true,
 *   });
 */
export function withInteractionTracking<P extends object>(
  Component: React.ComponentType<P>,
  options: WithTrackingOptions = {}
): React.FC<P> {
  const {
    type = "navigation",
    name = Component.displayName || Component.name || "Unknown",
    trackLifecycle = true,
    trackClicks = false,
    metadata,
  } = options;

  const TrackedComponent: React.FC<P> = (props) => {
    const interactionIdRef = useRef<string | null>(null);
    const containerRef = useRef<HTMLDivElement>(null);

    // Lifecycle tracking
    useEffect(() => {
      if (!trackLifecycle) return;

      interactionIdRef.current = logger.start(
        type,
        { element: "component", component: name },
        { ...metadata, props: Object.keys(props) }
      );

      return () => {
        if (interactionIdRef.current) {
          logger.end(interactionIdRef.current);
          interactionIdRef.current = null;
        }
      };
    }, []);

    // Click tracking
    useEffect(() => {
      if (!trackClicks || !containerRef.current) return;

      const handleClick = (e: MouseEvent) => {
        const target = e.target as HTMLElement;
        const elementName =
          target.id || target.className || target.tagName.toLowerCase();

        logger.start(
          "click",
          {
            element: elementName,
            component: name,
          },
          {
            ...metadata,
            clickedElement: target.outerHTML.slice(0, 100),
          }
        );
        // Clicks are fire-and-forget (no end needed for simple clicks)
      };

      const container = containerRef.current;
      container.addEventListener("click", handleClick);

      return () => {
        container.removeEventListener("click", handleClick);
      };
    }, [name, trackClicks, metadata]);

    if (trackClicks) {
      return (
        <div ref={containerRef} data-tracking={name}>
          <Component {...props} />
        </div>
      );
    }

    return <Component {...props} />;
  };

  TrackedComponent.displayName = `withInteractionTracking(${name})`;
  return TrackedComponent;
}
