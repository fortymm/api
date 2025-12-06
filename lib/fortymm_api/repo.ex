defmodule FortymmApi.Repo do
  use Ecto.Repo,
    otp_app: :fortymm_api,
    adapter: Ecto.Adapters.Postgres
end
