defmodule FortymmApiWeb.Plugs.RateLimiter do
  @moduledoc """
  Rate limiting plug using Hammer with ETS backend.

  Limits requests by IP address, with support for Fly.io's client IP header.
  """

  import Plug.Conn

  def init(opts) do
    %{
      limit: Keyword.get(opts, :limit, 10),
      interval_ms: Keyword.get(opts, :interval_ms, 60_000),
      id_prefix: Keyword.get(opts, :id_prefix, "rate_limit")
    }
  end

  def call(conn, opts) do
    ip = get_client_ip(conn)
    bucket_id = "#{opts.id_prefix}:#{ip}"

    case Hammer.check_rate(bucket_id, opts.interval_ms, opts.limit) do
      {:allow, count} ->
        put_rate_limit_headers(conn, opts.limit, count, opts.interval_ms)

      {:deny, limit} ->
        conn
        |> put_rate_limit_headers(limit, limit, opts.interval_ms)
        |> put_status(:too_many_requests)
        |> Phoenix.Controller.json(%{
          error: "Rate limit exceeded",
          message: "Too many requests. Please try again later."
        })
        |> halt()
    end
  end

  defp get_client_ip(conn) do
    # Trust Fly-Client-IP header
    case get_req_header(conn, "fly-client-ip") do
      [ip | _] ->
        ip

      [] ->
        case conn.remote_ip do
          {a, b, c, d} -> "#{a}.#{b}.#{c}.#{d}"
          ip -> to_string(ip)
        end
    end
  end

  defp put_rate_limit_headers(conn, limit, current, interval_ms) do
    remaining = max(limit - current, 0)
    reset_time = System.system_time(:second) + div(interval_ms, 1000)

    conn
    |> put_resp_header("x-ratelimit-limit", to_string(limit))
    |> put_resp_header("x-ratelimit-remaining", to_string(remaining))
    |> put_resp_header("x-ratelimit-reset", to_string(reset_time))
  end
end
