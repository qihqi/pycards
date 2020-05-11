port module Main exposing (..)

import Set exposing (Set, insert, remove)
import Array
import Browser
import Dict
import Debug
import Html exposing (Html, button, div, text, h2, h3, h4, hr, span, input, form, img, p)
import Html.Events exposing (onClick, on, onInput, onCheck)
import Browser.Events exposing (onKeyDown)
import Html.Attributes exposing (class, id, style, attribute, name, value, type_, placeholder, checked)
import String

import Json.Encode as Encode
import Json.Decode as Decode exposing (Decoder, int, string, list, maybe, field, andThen, at, nullable)
import Json.Decode.Pipeline exposing (required, optional)


port sendMessage : String -> Cmd msg
port messageReceiver: (String -> msg) -> Sub msg

type GameStatus = NO_NAME | IDLE | OBSERVING | PLAYING

type alias Player =
  { name : String
  , score: Int
  }

decodePlayer : Decoder Player
decodePlayer =
  Decode.succeed Player
    |> required "name" string
    |> required "score" int

type alias Game =
    { table :  List (String, List Int)
    , deck_count : Int
    }

addToDeckCount : Int -> Game -> Game
addToDeckCount deck game = {
    game | deck_count = game.deck_count + deck }

addToTable : (String, List Int) -> Game -> Game
addToTable play game = {
    game | table = List.append game.table [play]}

cleanTable : Game -> Game
cleanTable game = {game | table = []}

decodeTuple =
  Decode.map2 Tuple.pair
    (Decode.index 0 string)
    (Decode.index 1 (list int))

decodeGame : Decoder Game
decodeGame =
  Decode.succeed Game
    |> required "table" (list decodeTuple)
    |> required "deck_count" int


type alias Room =
    { game : Maybe Game
    , players : List Player
    , observers : List Player
    , current_player : Maybe Player
    , moderator_name: String
    }

decodeRoom : Decoder Room
decodeRoom =
  Decode.succeed Room
   |> optional "game" (maybe decodeGame) Nothing
   |> required "players" (list decodePlayer)
   |> required "observers" (list decodePlayer)
   |> optional "current_player" (maybe decodePlayer) Nothing
   |> required "moderator_name" string


type alias Model =
    { room: Maybe Room
    , status: GameStatus
    , auto_end_turn: Bool
    , hand: List Int
    , my_name: String
    , my_team: String
    , messages: List String
    , draft: String
    , table_selected: Set Int
    , hand_selected: Set Int
    , room_code: String
    , master_input: String
    , trump_num: Int
    , trump_suite: Int 
    }

modifyRoom : (Room -> Room) -> Model -> Model
modifyRoom func model = { model | room = Maybe.map func model.room}

modifyGame : (Game -> Game) -> Model -> Model
modifyGame func = modifyRoom
  (\r -> { r | game = Maybe.map func r.game })


decodeHand = list int

init_state : () -> (Model, Cmd msg)
init_state _ =
    ( { room = Nothing
        , status = NO_NAME
        , auto_end_turn = False
        , hand = []
        , my_name = ""
        , my_team = ""
        , messages = []
        , draft = ""
        , hand_selected = Set.empty
        , table_selected = Set.empty
        , room_code = ""
        , master_input = ""
        , trump_num = 0
        , trump_suite = 0 
        }
        , Cmd.none
    )


main =
    Browser.element
      { init =init_state
      , update = update
      , view = view
      , subscriptions = subscriptions
      }

type Msg =
    UI UIAction
    | TableSelect Int Bool
    | HandSelect Int Bool
    | Send
    | DraftChanged String
    | Incoming String
    | InputFieldChanged (String -> Model -> Model) String
    | SetTrumpSuite Int
    | None

type UIAction =
    DRAW | PLAY | TAKE_BACK | RETURN_TO_DECK |
    CLEAN_TABLE | END_TURN | TAKE_TURN | REFRESH | NEW_PLAYER |
    JOIN_ROOM | NEW_ROOM | NEW_GAME | SPREAD_CARDS | JOIN_GAME



update : Msg -> Model -> (Model, Cmd Msg)
update msg model =
  case msg of
    Send -> ({model | draft = ""}, sendMessage (makeChatMessage model.my_name model.draft))

    DraftChanged m -> ({model | draft = m}, Cmd.none)

    HandSelect cardId isAdd ->
      ( { model | hand_selected =
           if isAdd
              then (insert cardId model.hand_selected)
              else (remove cardId model.hand_selected)
        }
        , Cmd.none
      )

    TableSelect cardId isAdd ->
      ( { model | table_selected =
           if isAdd
              then (insert cardId model.table_selected)
              else (remove cardId model.table_selected)
        }
        , Cmd.none
      )

    UI action -> (makeNewModel action model,
                  makeAction action model |> sendMessage)
    Incoming message ->
        ( case (Decode.decodeString (execAction model) message) of
            Ok m -> m
            Err e -> Debug.log (Decode.errorToString e) model
        , Cmd.none
        )
    InputFieldChanged modifier message -> (modifier message model, Cmd.none)
    SetTrumpSuite newsuite -> ( {model | trump_suite = newsuite}, Cmd.none)
    _ -> (model, Cmd.none)

makeNewModel : UIAction -> Model -> Model
makeNewModel action model =
  case action of
    PLAY ->
      { model | hand = List.filter
            (\x -> not <| Set.member x model.hand_selected)
            model.hand
      }
    RETURN_TO_DECK ->
      { model | hand = List.filter
            (\x -> not <| Set.member x model.hand_selected)
            model.hand
      }
    NEW_PLAYER -> 
      { model | status = IDLE }
    _ -> model


makeAction : UIAction -> Model -> String
makeAction action model =
  let msg = case action of
        DRAW ->
          Encode.object
            [ ("name", Encode.string model.my_name)
            , ("action", Encode.string "DRAW")
            , ("arg", Encode.object [("num_cards", Encode.int 1)])
            ]
        PLAY ->
          Encode.object
            [ ("name", Encode.string model.my_name)
            , ("action", Encode.string "PLAY")
            , ("arg", Encode.object
                [ ("cards", Encode.list Encode.int (Set.toList model.hand_selected)) ])
            ]

        TAKE_BACK ->
          Encode.object
            [ ("name", Encode.string model.my_name)
            , ("action", Encode.string "TAKE_BACK")
            , ("arg", Encode.object
                [ ("cards", Encode.list Encode.int (Set.toList model.table_selected)) ])
            ]
        RETURN_TO_DECK ->
          Encode.object
            [ ("name", Encode.string model.my_name)
            , ("action", Encode.string "RETURN_TO_DECK")
            , ("arg", Encode.object
                [ ("cards", Encode.list Encode.int (Set.toList model.hand_selected)) ])
            ]
        CLEAN_TABLE ->
          Encode.object
            [ ("name", Encode.string model.my_name)
            , ("action", Encode.string "CLEAN_TABLE")
            , ("arg", Encode.string "")
            ]
        END_TURN ->
          Encode.object
            [ ("name", Encode.string model.my_name)
            , ("action", Encode.string "END_TURN")
            , ("arg", Encode.string "")
            ]
        TAKE_TURN ->
          Encode.object
            [ ("name", Encode.string model.my_name)
            , ("action", Encode.string "TAKE_TURN")
            , ("arg", Encode.string "")
            ]
        REFRESH ->
          Encode.object
            [ ("name", Encode.string model.my_name)
            , ("action", Encode.string "GET_STATE")
            , ("arg", Encode.string "")
            ]
        NEW_PLAYER -> 
          Encode.object 
            [ ("name", Encode.string model.my_name)
            , ("action", Encode.string "NEW_PLAYER")
            , ("arg", Encode.string model.my_name)
            ]
        NEW_ROOM -> 
          Encode.object 
            [ ("name", Encode.string model.my_name)
            , ("action", Encode.string "NEW_ROOM")
            , ("arg", Encode.string model.room_code)
            ]
        JOIN_ROOM -> 
          Encode.object 
            [ ("name", Encode.string model.my_name)
            , ("action", Encode.string "JOIN_ROOM")
            , ("arg", Encode.string model.room_code)
            ]
        NEW_GAME ->
          Encode.object 
            [ ("name", Encode.string model.my_name)
            , ("action", Encode.string "START")
            , ("arg", Encode.object 
                [("num_decks", Encode.int (String.toInt model.master_input |> Maybe.withDefault 0))]
              )
            ]
        SPREAD_CARDS ->
          Encode.object 
            [ ("name", Encode.string model.my_name)
            , ("action", Encode.string "SPREAD_CARDS")
            , ("arg", Encode.int (String.toInt model.master_input |> Maybe.withDefault 0))
            ]
        JOIN_GAME ->
          Encode.object 
            [ ("name", Encode.string model.my_name)
            , ("action", Encode.string "JOIN_GAME")
            , ("arg", Encode.string "")
            ]
          
  in Encode.encode 0 msg

makeChatMessage my_name message =
  Encode.encode 0 (Encode.object
            [ ("name", Encode.string my_name)
            , ("action", Encode.string "MESSAGE")
            , ("arg", Encode.string message)
            ] )

inputNameField =
    div [id "start_area"]
    [ h2 [class "center"] [ text "欢迎来打牌"]
    , p [class "center"] 
        [ input 
          [ placeholder "NAME", id "name", type_ "text"
          , onInput (InputFieldChanged (\t m -> {m | my_name = t }))
          ]
          []
        , button [id "connect", onClick (UI NEW_PLAYER) ][text "登陆"]
        ]
    ]

joinGameField model = 
    div [id "start_area"]
    [ h2 [class "center"] [ text ("欢迎来打牌: " ++ model.my_name)]
    , p [class "center"] 
        [ input 
          [ placeholder "Room Code"
          , type_ "text"
          , id "room_code"
          , value model.room_code
          , onInput (InputFieldChanged (\t m -> {m | room_code = t }))
          ]
          []
        , button [onClick (UI NEW_ROOM)][text "创建游戏"]
        , button [onClick (UI JOIN_ROOM)][text "加入游戏"]
        ]
    ]

getDeckCountStr : Room -> String
getDeckCountStr room = 
  case room.game of 
    Just game -> String.fromInt game.deck_count
    Nothing -> ""

getTable room = 
  case room.game of 
    Just game -> game.table
    Nothing -> []
  

view model  =
  if model.status == NO_NAME then inputNameField
  else (case model.room of
    Nothing -> joinGameField model
    Just room ->
        let
          turnText =
              case room.current_player of
                Nothing -> ""
                Just p -> if p.name == model.my_name then
                      "YOUR TURN"
                    else
                      p.name ++ "'s turn"
        in
            div []
            [ div [ id "chat_area"]
                  [  div [id "chat_text"]
                         (List.map (\x -> p [] [text x]) model.messages)
                  ,  input
                       [ id "chat_window"
                       , attribute "placeholder" "请尬料"
                       , onInput DraftChanged
                       , on "keydown" (ifIsEnter Send)
                       , value model.draft
                       ]
                      []
                  ]
            , div [ id "table_area" ]
                  [ h4 [] [ text "Players:"]
                  , div [class "row", id "players"]
                      (List.map
                        (\p ->  div [class "col-sm"]
                           [ text (p.name ++ "(" ++ (String.fromInt p.score) ++ ")")])
                        room.players)
                  , h4 [] [text ("牌组还剩：" ++ (getDeckCountStr room) ++"张")]
                  , h4 [id "turn"] [text turnText]
                  , h3 [] [ text "桌面:"]
                  , div [class "row", id "table"] 
                     (List.map (makeTableCard model.table_selected) <| getTable room)
                  , hr [] []
                  ]
            , div [id "hand_area"]
                  [ h3 [][text <| "手牌 (" ++ (String.fromInt <| List.length model.hand) ++ "):"]
                  , div [class "mygrid", id "hand"] ( 
                    model.hand 
                    |> List.sortBy (cardToSuiteValue model.trump_suite model.trump_num)
                    |> List.map (makeCard True model.hand_selected))
                  ]
            , controlArea (model.my_name == room.moderator_name)
            ])

makeTableCard : Set Int -> (String, List Int) -> Html Msg
makeTableCard selectedSet (player_name, cards) =
  let
    width = (50 * (List.length cards) + 50 + max 20 (10 * (String.length player_name)))
  in div
    [ class "player_table",  style "width" <| (String.fromInt width ++ "px")]
    [ div [class "mygrid"]
      <| (List.map (makeCard False selectedSet) cards)
    , span [class "player_name"]
       [text player_name]
    ]


makeCard : Bool -> Set Int -> Int -> Html Msg
makeCard isHand selectedSet cardValue =
  let
    isSelected = Set.member cardValue selectedSet
    selectEvent = (if isHand then HandSelect else TableSelect)
  in
      div [class "one_card"]
        [ input
              [type_ "checkbox"
              , class (if isHand then "hand_card" else "table_card")
              , attribute "card_id" <| String.fromInt cardValue
              , checked isSelected
              , onCheck (selectEvent cardValue)
              ] []
        , text <| cardText cardValue
        , img [ attribute "height" "120"
              , attribute "src" <| Maybe.withDefault "" <| Array.get (modBy 54 cardValue) cardImgUrls
              , onClick <| (selectEvent cardValue (not isSelected))
              ] []
        ]


controlArea enableMaster =
   div -- control area
      [id "control_area", style "vertical-align" "text-top"]
      [ input [type_ "checkbox", id "auto_end_turn", attribute "checked" ""]
            []
      , text "自动结束回合"
      , button [ class "turn_control", id "draw", onClick (UI DRAW)]
           [ text "摸牌(z)" ]
      , button [ class "turn_control", id "takeback", onClick (UI TAKE_BACK) ]
            [ text "拿回来" ]
      , button [ class "turn_control", id "return_to_deck", onClick (UI RETURN_TO_DECK) ]
            [ text "放回牌组" ]
      , button [ class "turn_control", id "end_turn", onClick (UI END_TURN) ]
            [ text "结束回合" ]
      , button [ id "refresh", onClick (UI REFRESH) ]
            [ text "刷新" ]
      , button [onClick (UI JOIN_GAME) ]
            [ text "从新加入" ]
      , button [ class "turn_control", id "send",  onClick (UI PLAY)]
            [ text "出牌(b)" ]
      , button [ class "turn_control", id "clear_table", onClick (UI CLEAN_TABLE) ]
            [ text "清空桌面(n)" ]
      , button [ id "take_turn", onClick (UI TAKE_TURN) ]
            [ text "该我了(m)" ]
      , form [ id "sort_form" ]
            [ span [][ text "主花色" ]
            , input
                [  attribute "checked" ""
                , class "suite_radio"
                , name "suite"
                , type_ "radio"
                , value "S"
                , onClick (SetTrumpSuite 3)
                ] []
            , span [ attribute "style" "font-size:30px" ]
                       [ text "♠" ]
            , input
                [  attribute "checked" ""
                , class "suite_radio"
                , name "suite"
                , type_ "radio"
                , value "H"
                , onClick (SetTrumpSuite 2)
                ] []
            , span [ attribute "style" "font-size:30px" ]
                       [ text "♥" ]
            , input
                [  attribute "checked" ""
                , class "suite_radio"
                , name "suite"
                , type_ "radio"
                , value "D"
                , onClick (SetTrumpSuite 0)
                ] []
            , span [ attribute "style" "font-size:30px" ]
                       [ text "♣" ]
            , input
                [  attribute "checked" ""
                , class "suite_radio"
                , name "suite"
                , type_ "radio"
                , value "C"
                , onClick (SetTrumpSuite 1)
                ] []
            , span [ attribute "style" "font-size:30px" ]
                       [ text "♦" ]
            , span [][text "主数字"]
            , input 
              [onInput (InputFieldChanged 
                (\t m -> {m | trump_num = Maybe.withDefault 0 <| String.toInt t}))]
              []
            ]
      ,  if enableMaster then
          div [ class "master", id "master_control" ]
            [ button [ class "master", id "new_game", onClick (UI NEW_GAME)]
                [ text "新游戏" ]
            , button [ class "master", id "end_draw" ]
                [ text "停止摸牌" ]
            , button [ class "master", id "spread_cards", onClick (UI SPREAD_CARDS) ]
                [ text "发牌" ]
            , button [ class "master", id "deal_from_deck" ]
                [ text "翻牌" ]
            , input 
               [class "master", id "spread_count", placeholder "几张" 
               , onInput (InputFieldChanged (\t m -> {m | master_input = t}))
               ]
               []
            ]
          else text ""
      ]

cardToSuiteValue : Int -> Int -> Int -> (Int, Int)
cardToSuiteValue tsuite tval card_val = 
  let 
    val = card_val |> modBy 54 |> modBy 13
    suite = card_val |> modBy 54 |> (\x -> x // 13)
    val2 = 
      if (suite == 4) then --joker
          val + 20
      else if val == (tval - 2) && (suite == tsuite) then --suite num
          16 
      else if (val == tval - 2) then -- just num
          15
      else
          val
    suite2 = 
      if suite == tsuite || val == tval - 2 then 
          4
      else 
          suite
  in (suite2, val2)


execAction : Model -> Decode.Decoder Model
execAction model =
   let
     room = model.room
     game = case model.room of 
       Just r -> r.game
       Nothing -> Nothing
   in
       (field "action" string) |>
          andThen (\action ->
            (field "name" string) |>
              andThen( \name ->
                  case action of
                      "DRAWED" ->
                        (field "arg" decodeHand) |>
                            andThen (\cards ->
                               Decode.succeed
                                 {model | hand = model.hand ++ cards})
                      "DRAW" ->
                         (decodeArgAndGet "num_cards" int) |>
                          andThen (\c ->
                                 model
                                   |> modifyGame (addToDeckCount (-c))
                                   |> Decode.succeed )
                      "CLEAN_TABLE" ->
                         model
                           |> modifyGame cleanTable
                           |> Decode.succeed

                      "PLAY" ->
                        (decodeArgAndGet "cards" (list int)) |>
                        andThen ( \c ->
                                     model
                                       |> modifyGame (addToTable (name, c))
                                       |> Decode.succeed )
                      "RETURN_TO_DECK" ->
                         (decodeArgAndGet "num_cards" int) |>
                          andThen (\c ->
                                     model
                                       |> modifyGame (addToDeckCount c)
                                       |> Decode.succeed )

                      "TAKE_TURN" ->
                         model
                           |> modifyRoom (\r ->
                              {r | current_player =
                                 List.head (List.filter (\x -> x.name == name) r.players)
                              })
                           |> Decode.succeed
                      "PLAYER_LEFT" ->
                        model
                          |> modifyRoom(\r ->
                            {r | players = List.filter
                                 (\x -> x.name /= name) r.players,
                               observers = List.filter
                                 (\x -> x.name /= name) r.observers})
                          |> Decode.succeed
                      "ADD_POINTS" ->
                         (decodeArgAndGet "points" int) |>
                         andThen (\score ->
                             model
                              |> modifyRoom(\r ->
                                {r | players = List.map
                                     (\x -> if x.name == name
                                       then {x | score = x.score + score }
                                       else x
                                     ) r.players})
                              |> Decode.succeed
                              )
                      "SET_STATE" ->
                        (at ["arg", "room"] (maybe decodeRoom))
                        |> andThen (\newroom ->
                            maybe (at ["arg", "hand"] decodeHand)
                            |> andThen ( \newhand ->
                              Decode.succeed
                                 {model |
                                   room = newroom
                                 , hand = case newhand of
                                     Just h -> h
                                     Nothing -> model.hand
                                 }))

                      "GET_STATE" ->
                         Decode.succeed model
                      "MESSAGE" -> 
                        (field "arg" string)
                        |> andThen ( \m -> 
                             Decode.succeed 
                               { model | messages = model.messages 
                                 ++ [name ++ ": " ++ m] })
                      _ -> Decode.fail action
                  ))


decodeArgAndGet : String -> Decoder a -> Decoder a
decodeArgAndGet key decoder_type =
  (field "arg" (Decode.dict decoder_type)) |>
    andThen ( \arg -> case (Dict.get key arg) of
      Just value -> Decode.succeed value
      Nothing -> Decode.fail key)


subscriptions : Model -> Sub Msg
subscriptions model = messageReceiver (handleIncomingEvents model)

controlKeys = Dict.fromList 
  [  ("z", DRAW)
  ,  ("b", PLAY)
  ,  ("n", CLEAN_TABLE)
  ,  ("m", END_TURN)
  ]
cardSelectKeys = [
    "1",  "2",  "3",  "4",  "5",  "6",  "7",  "8",  "9",  "0",  "-",  "=",
    "q",  "w",  "e",  "r",  "t",  "y",  "u",  "i",  "o",  "p",  "[",  "]",
    "a",  "s",  "d",  "f",  "g",  "h",  "j",  "k",  ";",  "'"] 
    |> List.indexedMap (\x y -> (y, x))
    |> Dict.fromList


handleIncomingEvents : Model -> String -> Msg
handleIncomingEvents model msg = 
  case (Decode.decodeString (field "key" string) msg) of
    Ok key -> case Dict.get key controlKeys of
      Just e -> UI e
      Nothing -> case Dict.get key cardSelectKeys of
        Just e -> case Array.get e
                        (model.hand 
                        |> List.sortBy (cardToSuiteValue model.trump_suite model.trump_num)
                        |> Array.fromList)
            of 
                Just card ->
                   HandSelect card <| not (Set.member card model.hand_selected)
                Nothing -> None
        Nothing -> None
    Err _ -> Incoming msg

ifIsEnter msg =
  Decode.field "key" Decode.string
    |> Decode.andThen (\key -> if key == "Enter" then Decode.succeed msg else Decode.fail "some other key")

--TODO
suites = Array.fromList ["♠", "♥", "♣", "♦"]
cardText : Int -> String
cardText cardv = 
  let 
    suite = cardv |> modBy 54 |> (\x -> x // 13)
    val = cardv |> modBy 54 |> modBy 13
  in
    if suite == 4 then
        if val == 0 then "小" else "大"
    else
        (Maybe.withDefault "" <| Array.get suite suites) ++ (String.fromInt val)


cardImgUrls = Array.fromList
    [ "/static/2C.png"
    , "/static/3C.png"
    , "/static/4C.png"
    , "/static/5C.png"
    , "/static/6C.png"
    , "/static/7C.png"
    , "/static/8C.png"
    , "/static/9C.png"
    , "/static/0C.png"
    , "/static/JC.png"
    , "/static/QC.png"
    , "/static/KC.png"
    , "/static/AC.png"
    , "/static/2D.png"
    , "/static/3D.png"
    , "/static/4D.png"
    , "/static/5D.png"
    , "/static/6D.png"
    , "/static/7D.png"
    , "/static/8D.png"
    , "/static/9D.png"
    , "/static/0D.png"
    , "/static/JD.png"
    , "/static/QD.png"
    , "/static/KD.png"
    , "/static/AD.png"
    , "/static/2H.png"
    , "/static/3H.png"
    , "/static/4H.png"
    , "/static/5H.png"
    , "/static/6H.png"
    , "/static/7H.png"
    , "/static/8H.png"
    , "/static/9H.png"
    , "/static/0H.png"
    , "/static/JH.png"
    , "/static/QH.png"
    , "/static/KH.png"
    , "/static/AH.png"
    , "/static/2S.png"
    , "/static/3S.png"
    , "/static/4S.png"
    , "/static/5S.png"
    , "/static/6S.png"
    , "/static/7S.png"
    , "/static/8S.png"
    , "/static/9S.png"
    , "/static/0S.png"
    , "/static/JS.png"
    , "/static/QS.png"
    , "/static/KS.png"
    , "/static/AS.png"
    , "/static/joker.jpg"
    , "/static/XX.png"
    ]

