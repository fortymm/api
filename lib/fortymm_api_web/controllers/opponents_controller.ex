defmodule FortymmApiWeb.OpponentsController do
  use FortymmApiWeb, :controller

  @fake_opponents [
    %{
      id: "user-001",
      username: "TableTennisKing",
      avatarUrl: "https://api.dicebear.com/7.x/avataaars/svg?seed=TableTennisKing",
      isEphemeral: false,
      headToHead: %{wins: 5, losses: 3},
      lastMatch: %{
        id: "match-101",
        result: "win",
        score: "11-9, 11-7, 9-11, 11-5",
        playedAt: "2025-12-01T14:30:00Z"
      }
    },
    %{
      id: "user-002",
      username: "PingPongPro",
      avatarUrl: "https://api.dicebear.com/7.x/avataaars/svg?seed=PingPongPro",
      isEphemeral: false,
      headToHead: %{wins: 2, losses: 4},
      lastMatch: %{
        id: "match-098",
        result: "loss",
        score: "9-11, 11-8, 7-11, 11-13",
        playedAt: "2025-11-28T18:00:00Z"
      }
    },
    %{
      id: "user-003",
      username: "SpinMaster42",
      avatarUrl: nil,
      isEphemeral: false,
      headToHead: %{wins: 1, losses: 1},
      lastMatch: %{
        id: "match-095",
        result: "win",
        score: "11-6, 11-4, 11-8",
        playedAt: "2025-11-25T10:15:00Z"
      }
    },
    %{
      id: "user-004",
      username: "BackhandQueen",
      avatarUrl: "https://api.dicebear.com/7.x/avataaars/svg?seed=BackhandQueen",
      isEphemeral: false,
      headToHead: %{wins: 0, losses: 2}
    },
    %{
      id: "user-005",
      username: "LoopDriveLarry",
      avatarUrl: "https://api.dicebear.com/7.x/avataaars/svg?seed=LoopDriveLarry",
      isEphemeral: false,
      lastMatch: %{
        id: "match-090",
        result: "loss",
        score: "5-11, 8-11, 6-11",
        playedAt: "2025-11-20T16:45:00Z"
      }
    },
    %{
      id: "user-006",
      username: "ChopBlockChamp",
      avatarUrl: "https://api.dicebear.com/7.x/avataaars/svg?seed=ChopBlockChamp",
      isEphemeral: false,
      headToHead: %{wins: 3, losses: 3},
      lastMatch: %{
        id: "match-088",
        result: "win",
        score: "11-9, 9-11, 11-7, 8-11, 11-9",
        playedAt: "2025-11-18T19:30:00Z"
      }
    },
    %{
      id: "user-007",
      username: "ServeAce",
      avatarUrl: nil,
      isEphemeral: false
    },
    %{
      id: "user-008",
      username: "ForehandFlick",
      avatarUrl: "https://api.dicebear.com/7.x/avataaars/svg?seed=ForehandFlick",
      isEphemeral: true,
      headToHead: %{wins: 1, losses: 0},
      lastMatch: %{
        id: "match-085",
        result: "win",
        score: "11-3, 11-5, 11-2",
        playedAt: "2025-11-15T11:00:00Z"
      }
    },
    %{
      id: "user-009",
      username: "RallyRuler",
      avatarUrl: "https://api.dicebear.com/7.x/avataaars/svg?seed=RallyRuler",
      isEphemeral: false,
      headToHead: %{wins: 7, losses: 8},
      lastMatch: %{
        id: "match-082",
        result: "loss",
        score: "11-13, 9-11, 11-8, 10-12",
        playedAt: "2025-11-12T20:00:00Z"
      }
    },
    %{
      id: "user-010",
      username: "SmashBros",
      avatarUrl: "https://api.dicebear.com/7.x/avataaars/svg?seed=SmashBros",
      isEphemeral: false,
      headToHead: %{wins: 4, losses: 2},
      lastMatch: %{
        id: "match-080",
        result: "win",
        score: "11-7, 11-9, 11-6",
        playedAt: "2025-11-10T14:00:00Z"
      }
    }
  ]

  def index(conn, params) do
    query = Map.get(params, "query", "")
    limit = parse_limit(Map.get(params, "limit", "50"))

    opponents =
      @fake_opponents
      |> filter_by_query(query)
      |> Enum.take(limit)

    json(conn, %{
      opponents: opponents,
      query: if(query == "", do: nil, else: query),
      total: length(opponents)
    })
  end

  defp filter_by_query(opponents, "") do
    opponents
  end

  defp filter_by_query(opponents, query) do
    query_downcase = String.downcase(query)

    Enum.filter(opponents, fn opponent ->
      String.contains?(String.downcase(opponent.username), query_downcase)
    end)
  end

  defp parse_limit(limit) when is_binary(limit) do
    case Integer.parse(limit) do
      {num, _} -> min(max(num, 1), 100)
      :error -> 50
    end
  end

  defp parse_limit(limit) when is_integer(limit), do: min(max(limit, 1), 100)
  defp parse_limit(_), do: 50
end
