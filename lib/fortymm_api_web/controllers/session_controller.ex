defmodule FortymmApiWeb.SessionController do
  use FortymmApiWeb, :controller

  alias FortymmApi.Accounts

  @session_cookie_name "fortymm_session"
  @session_cookie_options [
    http_only: true,
    secure: Application.compile_env(:fortymm_api, :session_cookie_secure, true),
    same_site: "Lax",
    # 10 years in seconds
    max_age: 315_360_000
  ]

  def index(conn, _params) do
    conn = fetch_cookies(conn)

    case get_existing_session(conn) do
      {:ok, user} ->
        render_session(conn, user)

      :error ->
        # Auto-create anonymous user
        case Accounts.create_anonymous_user() do
          {:ok, user} ->
            token = Accounts.generate_user_session_token(user)

            conn
            |> put_resp_cookie(@session_cookie_name, token, @session_cookie_options)
            |> render_session(user)

          {:error, _changeset} ->
            conn
            |> put_status(:internal_server_error)
            |> json(%{error: "Failed to create session"})
        end
    end
  end

  defp get_existing_session(conn) do
    with token when not is_nil(token) <- conn.cookies[@session_cookie_name],
         {user, _inserted_at} when not is_nil(user) <-
           Accounts.get_user_by_session_token(token) do
      {:ok, user}
    else
      _ -> :error
    end
  end

  defp render_session(conn, user) do
    json(conn, %{
      username: user.username,
      email: user.email,
      has_password: not is_nil(user.hashed_password)
    })
  end
end
