defmodule FortymmApiWeb.SessionController do
  use FortymmApiWeb, :controller

  def index(conn, _params) do
    conn = fetch_cookies(conn)

    case conn.cookies["auth"] do
      nil ->
        create_session(conn)

      token ->
        case Phoenix.Token.verify(FortymmApiWeb.Endpoint, "auth", token) do
          {:ok, _data} ->
            json(conn, %{username: "Guest"})

          {:error, _reason} ->
            create_session(conn)
        end
    end
  end

  defp create_session(conn) do
    token = Phoenix.Token.sign(FortymmApiWeb.Endpoint, "auth", "guest")

    conn
    |> put_resp_cookie("auth", token, http_only: true)
    |> json(%{username: "Guest"})
  end
end
