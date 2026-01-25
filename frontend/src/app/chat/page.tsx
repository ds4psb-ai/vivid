"use client";
/* eslint-disable @next/next/no-img-element */

import { useEffect, useState } from "react";
import Link from "next/link";
import { MessageCircle, Users, TrendingUp, Clock, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";

// Types
interface ChatIP {
  id: string;
  slug: string;
  name_ko: string;
  name_en: string;
  thumbnail_url: string | null;
  chat_enabled: boolean;
  chat_model_default: string;
  chat_session_count: number;
  chat_message_count: number;
}

interface ChatSession {
  id: string;
  ip_id: string;
  ip_name: string;
  ip_thumbnail: string | null;
  title: string | null;
  scenario_branch: string | null;
  model_preference: string;
  total_messages: number;
  total_credits_spent: number;
  is_pinned: boolean;
  is_archived: boolean;
  created_at: string;
  last_message_at: string | null;
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8100";

export default function ChatListPage() {
  const [ips, setIps] = useState<ChatIP[]>([]);
  const [recentSessions, setRecentSessions] = useState<ChatSession[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"characters" | "history">("characters");

  // Fetch chat-enabled IPs
  useEffect(() => {
    async function fetchIPs() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/chat/ips?limit=20`, {
          credentials: "include",
        });
        if (res.ok) {
          const data = await res.json();
          setIps(data);
        }
      } catch (err) {
        console.error("Failed to fetch IPs", err);
      }
    }

    fetchIPs();
  }, []);

  // Fetch recent sessions
  useEffect(() => {
    async function fetchSessions() {
      try {
        const res = await fetch(`${API_BASE}/api/v1/chat/sessions?page_size=10`, {
          credentials: "include",
        });
        if (res.ok) {
          const data = await res.json();
          setRecentSessions(data.sessions);
        }
      } catch (err) {
        console.error("Failed to fetch sessions", err);
      } finally {
        setIsLoading(false);
      }
    }

    fetchSessions();
  }, []);

  // Format relative time
  function formatRelativeTime(dateString: string | null) {
    if (!dateString) return "대화 없음";

    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return "방금 전";
    if (diffMins < 60) return `${diffMins}분 전`;
    if (diffHours < 24) return `${diffHours}시간 전`;
    if (diffDays < 7) return `${diffDays}일 전`;
    return date.toLocaleDateString("ko-KR");
  }

  // Format number with K/M suffix
  function formatNumber(num: number) {
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}K`;
    return num.toString();
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Header */}
      <header className="sticky top-0 z-10 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-4">
            IP 채팅
          </h1>

          {/* Tabs */}
          <div className="flex gap-2">
            <button
              onClick={() => setActiveTab("characters")}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                activeTab === "characters"
                  ? "bg-blue-500 text-white"
                  : "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
              )}
            >
              <Users className="w-4 h-4 inline-block mr-1" />
              캐릭터
            </button>
            <button
              onClick={() => setActiveTab("history")}
              className={cn(
                "px-4 py-2 rounded-lg text-sm font-medium transition-colors",
                activeTab === "history"
                  ? "bg-blue-500 text-white"
                  : "bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600"
              )}
            >
              <Clock className="w-4 h-4 inline-block mr-1" />
              대화 기록
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-6">
        {isLoading ? (
          <div className="space-y-4">
            {[...Array(4)].map((_, i) => (
              <div
                key={i}
                className="bg-white dark:bg-gray-800 rounded-xl p-4 animate-pulse"
              >
                <div className="flex items-center gap-4">
                  <div className="w-16 h-16 bg-gray-200 dark:bg-gray-700 rounded-full" />
                  <div className="flex-1">
                    <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-2" />
                    <div className="h-3 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : activeTab === "characters" ? (
          <>
            {/* Featured Characters */}
            {ips.length > 0 && (
              <section className="mb-8">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
                  <TrendingUp className="w-5 h-5 text-orange-500" />
                  인기 캐릭터
                </h2>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {ips.slice(0, 4).map((ip) => (
                    <Link
                      key={ip.id}
                      href={`/chat/${ip.id}`}
                      className="bg-white dark:bg-gray-800 rounded-xl p-4 hover:shadow-lg transition-shadow group"
                    >
                      <div className="flex items-center gap-4">
                        {ip.thumbnail_url ? (
                          <img
                            src={ip.thumbnail_url}
                            alt={ip.name_ko}
                            className="w-16 h-16 rounded-full object-cover"
                          />
                        ) : (
                          <div className="w-16 h-16 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white text-xl font-bold">
                            {ip.name_ko[0]}
                          </div>
                        )}

                        <div className="flex-1 min-w-0">
                          <h3 className="font-semibold text-gray-900 dark:text-white truncate group-hover:text-blue-500 transition-colors">
                            {ip.name_ko}
                          </h3>
                          <p className="text-sm text-gray-500 dark:text-gray-400">
                            {ip.name_en}
                          </p>
                          <div className="flex items-center gap-3 mt-1 text-xs text-gray-400">
                            <span className="flex items-center gap-1">
                              <MessageCircle className="w-3 h-3" />
                              {formatNumber(ip.chat_message_count)}
                            </span>
                            <span className="flex items-center gap-1">
                              <Users className="w-3 h-3" />
                              {formatNumber(ip.chat_session_count)}
                            </span>
                          </div>
                        </div>

                        <ChevronRight className="w-5 h-5 text-gray-400 group-hover:text-blue-500 transition-colors" />
                      </div>
                    </Link>
                  ))}
                </div>
              </section>
            )}

            {/* All Characters */}
            {ips.length > 4 && (
              <section>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                  모든 캐릭터
                </h2>

                <div className="space-y-2">
                  {ips.slice(4).map((ip) => (
                    <Link
                      key={ip.id}
                      href={`/chat/${ip.id}`}
                      className="flex items-center gap-4 bg-white dark:bg-gray-800 rounded-xl p-3 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors group"
                    >
                      {ip.thumbnail_url ? (
                        <img
                          src={ip.thumbnail_url}
                          alt={ip.name_ko}
                          className="w-12 h-12 rounded-full object-cover"
                        />
                      ) : (
                        <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white font-bold">
                          {ip.name_ko[0]}
                        </div>
                      )}

                      <div className="flex-1 min-w-0">
                        <h3 className="font-medium text-gray-900 dark:text-white truncate">
                          {ip.name_ko}
                        </h3>
                        <p className="text-sm text-gray-500 dark:text-gray-400">
                          {formatNumber(ip.chat_message_count)} 메시지
                        </p>
                      </div>

                      <ChevronRight className="w-5 h-5 text-gray-400" />
                    </Link>
                  ))}
                </div>
              </section>
            )}

            {ips.length === 0 && (
              <div className="text-center py-12">
                <MessageCircle className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  채팅 가능한 캐릭터가 없습니다
                </h3>
                <p className="text-gray-500 dark:text-gray-400">
                  곧 새로운 캐릭터가 추가될 예정입니다
                </p>
              </div>
            )}
          </>
        ) : (
          /* History Tab */
          <>
            {recentSessions.length > 0 ? (
              <div className="space-y-2">
                {recentSessions.map((session) => (
                  <Link
                    key={session.id}
                    href={`/chat/${session.ip_id}?session=${session.id}`}
                    className="flex items-center gap-4 bg-white dark:bg-gray-800 rounded-xl p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors group"
                  >
                    {session.ip_thumbnail ? (
                      <img
                        src={session.ip_thumbnail}
                        alt={session.ip_name}
                        className="w-12 h-12 rounded-full object-cover"
                      />
                    ) : (
                      <div className="w-12 h-12 rounded-full bg-gradient-to-br from-blue-400 to-purple-500 flex items-center justify-center text-white font-bold">
                        {session.ip_name[0]}
                      </div>
                    )}

                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-gray-900 dark:text-white truncate">
                        {session.ip_name}
                      </h3>
                      <p className="text-sm text-gray-500 dark:text-gray-400">
                        {session.total_messages} 메시지 &middot;{" "}
                        {formatRelativeTime(session.last_message_at)}
                      </p>
                    </div>

                    <div className="text-right">
                      <span
                        className={cn(
                          "text-xs px-2 py-0.5 rounded-full",
                          session.model_preference === "flash"
                            ? "bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200"
                            : session.model_preference === "pro"
                            ? "bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200"
                            : "bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200"
                        )}
                      >
                        {session.model_preference.toUpperCase()}
                      </span>
                      <p className="text-xs text-gray-400 mt-1">
                        {session.total_credits_spent} 크레딧
                      </p>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <div className="text-center py-12">
                <Clock className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
                  대화 기록이 없습니다
                </h3>
                <p className="text-gray-500 dark:text-gray-400 mb-4">
                  캐릭터와 대화를 시작해보세요
                </p>
                <button
                  onClick={() => setActiveTab("characters")}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                >
                  캐릭터 둘러보기
                </button>
              </div>
            )}
          </>
        )}
      </main>
    </div>
  );
}
