defmodule FortymmApiWeb.AccountController do
  use FortymmApiWeb, :controller

  alias FortymmApi.Accounts

  @session_cookie_name "fortymm_session"

  def update(conn, %{"username" => username}) do
    conn = fetch_cookies(conn)

    case get_current_user(conn) do
      {:ok, user} ->
        case Accounts.update_username(user, %{username: username}) do
          {:ok, updated_user} ->
            json(conn, %{
              username: updated_user.username,
              email: updated_user.email,
              has_password: not is_nil(updated_user.hashed_password)
            })

          {:error, changeset} ->
            conn
            |> put_status(:unprocessable_entity)
            |> json(%{errors: format_errors(changeset)})
        end

      :error ->
        conn
        |> put_status(:unauthorized)
        |> json(%{error: "Not authenticated"})
    end
  end

  def update(conn, _params) do
    conn
    |> put_status(:bad_request)
    |> json(%{error: "Missing required parameter: username"})
  end

  defp get_current_user(conn) do
    with token when not is_nil(token) <- conn.cookies[@session_cookie_name],
         {user, _inserted_at} when not is_nil(user) <-
           Accounts.get_user_by_session_token(token) do
      {:ok, user}
    else
      _ -> :error
    end
  end

  defp format_errors(changeset) do
    Ecto.Changeset.traverse_errors(changeset, fn {msg, opts} ->
      Regex.replace(~r"%{(\w+)}", msg, fn _, key ->
        opts |> Keyword.get(String.to_existing_atom(key), key) |> to_string()
      end)
    end)
  end
end
