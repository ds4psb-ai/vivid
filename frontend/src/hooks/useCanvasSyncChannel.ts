import { useCallback, useEffect, useRef } from "react";
import { CanvasSyncEvent, createCanvasSyncChannel } from "@/lib/canvasSync";

export const useCanvasSyncChannel = (
  onEvent?: (event: CanvasSyncEvent) => void,
): ((event: CanvasSyncEvent) => void) => {
  const channelRef = useRef<BroadcastChannel | null>(null);
  const handlerRef = useRef(onEvent);

  useEffect(() => {
    handlerRef.current = onEvent;
  }, [onEvent]);

  useEffect(() => {
    const channel = createCanvasSyncChannel();
    if (!channel) return;
    channelRef.current = channel;

    const handleMessage = (event: MessageEvent) => {
      if (!handlerRef.current) return;
      const payload = event.data as CanvasSyncEvent;
      if (!payload || typeof payload !== "object") return;
      if (!("type" in payload)) return;
      handlerRef.current(payload);
    };

    channel.addEventListener("message", handleMessage);
    return () => {
      channel.removeEventListener("message", handleMessage);
      channel.close();
      channelRef.current = null;
    };
  }, []);

  return useCallback((event: CanvasSyncEvent) => {
    channelRef.current?.postMessage(event);
  }, []);
};
